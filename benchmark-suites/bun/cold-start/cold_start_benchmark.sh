#!/bin/bash

# Скрипт для измерения времени холодного старта Bun в Docker-контейнере
# Измеряемые метрики:
# - Время запуска рантайма (T1 - T0)
# - Время первого запроса (T2 - T1)
# - Общее время холодного старта (T2 - T0)

# Версия скрипта
SCRIPT_VERSION="1.0.0"

# Парсинг аргументов командной строки
while getopts ":i:" opt; do
  case ${opt} in
    i )
      CUSTOM_ITERATIONS=$OPTARG
      ;;
    \? )
      echo "Неверный параметр: -$OPTARG" 1>&2
      echo "Использование: $0 [-i количество_итераций]" 1>&2
      exit 1
      ;;
    : )
      echo "Параметр -$OPTARG требует значение" 1>&2
      exit 1
      ;;
  esac
done

# Устанавливаем обработчики ошибок и прерываний
set -e
trap cleanup EXIT INT TERM

# Определяем имя контейнера с уникальным идентификатором - базовая часть
CONTAINER_NAME_BASE="bun-cold-start-benchmark"

# Имя образа
IMAGE_NAME="bun-cold-start-benchmark"

# Имя файла с результатами и начальная структура JSON
RESULTS_FILE="results/cold-start/bun_cold_start_benchmark_$(date +%Y%m%d_%H%M%S).json"

# Переменные для хранения статистики
declare -a STARTUP_TIMES
declare -a FIRST_REQUEST_TIMES
declare -a TOTAL_TIMES

# Количество итераций (по умолчанию 30, может быть переопределено через параметр -i)
ITERATIONS=${CUSTOM_ITERATIONS:-30}
echo "Количество итераций: $ITERATIONS"

# Максимальное время ожидания (в секундах)
MAX_WAIT_TIME=30

# Порт для тестирования
PORT=3001

# Функция для очистки ресурсов
cleanup() {
    echo "Очистка ресурсов..."
    # Останавливаем и удаляем все контейнеры с указанным именем
    docker ps -a | grep $CONTAINER_NAME_BASE | awk '{print $1}' | xargs -r docker rm -f > /dev/null 2>&1 || true
    echo "Очистка завершена"
}

# Функция для логирования с отметкой времени
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" >&2
}

# Функция для получения системной информации хоста
get_system_info() {
    log "Сбор информации о системе хоста..."
    local os_type=$(uname)
    local os_version=""
    local cpu_cores=""
    local memory_mb=""
    local cpu_model=""
    
    # Определяем детали ОС
    if [ "$os_type" = "Linux" ]; then
        os_version=$(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)
    elif [ "$os_type" = "Darwin" ]; then
        os_version=$(sw_vers -productVersion)
    else
        os_version="unknown"
    fi
    
    # Определяем модель CPU
    if [ "$os_type" = "Linux" ]; then
        cpu_model=$(cat /proc/cpuinfo | grep "model name" | head -n1 | cut -d':' -f2 | xargs)
    elif [ "$os_type" = "Darwin" ]; then
        cpu_model=$(sysctl -n machdep.cpu.brand_string)
    else
        cpu_model="unknown"
    fi
    
    # Определяем количество ядер CPU
    if [ "$os_type" = "Linux" ]; then
        cpu_cores=$(nproc)
    elif [ "$os_type" = "Darwin" ]; then
        cpu_cores=$(sysctl -n hw.ncpu)
    else
        cpu_cores="unknown"
    fi
    
    # Определяем объем оперативной памяти
    if [ "$os_type" = "Linux" ]; then
        memory_mb=$(free -m | grep Mem | awk '{print $2}')
    elif [ "$os_type" = "Darwin" ]; then
        memory_mb=$(($(sysctl -n hw.memsize) / 1024 / 1024))
    else
        memory_mb="unknown"
    fi
    
    # Возвращаем информацию в формате JSON
    echo "{\"os_type\":\"$os_type\",\"os_version\":\"$os_version\",\"cpu_model\":\"$cpu_model\",\"cpu_cores\":$cpu_cores,\"memory_mb\":$memory_mb}"
}

# Функция для получения информации о среде Bun в контейнере
get_bun_environment() {
    log "Сбор информации о среде выполнения Bun..."
    
    # Запускаем временный контейнер для сбора информации
    local container_id=$(docker run -d --name bun-env-info-$(date +%s) $IMAGE_NAME sleep 15)
    
    # Собираем информацию об ОС в контейнере
    local os_info=$(docker exec $container_id cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)
    
    # Собираем информацию о памяти, выделенной контейнеру (memory limit)
    local memory_limit=$(docker exec $container_id cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo "unknown")
    if [ "$memory_limit" != "unknown" ]; then
        memory_limit=$((memory_limit / 1024 / 1024))" MB"
    fi
    
    # Собираем информацию о CPU, выделенных контейнеру
    local cpu_shares=$(docker exec $container_id cat /sys/fs/cgroup/cpu/cpu.shares 2>/dev/null || echo "unknown")
    
    # Получаем настройки Bun
    local bun_config=$(docker exec $container_id bun --version 2>/dev/null)
    
    # Останавливаем и удаляем контейнер
    docker stop $container_id >/dev/null
    docker rm $container_id >/dev/null
    
    # Возвращаем информацию в формате JSON
    echo "{\"os\":\"$os_info\",\"memory_limit\":\"$memory_limit\",\"cpu_shares\":\"$cpu_shares\",\"bun_version\":\"$bun_config\"}"
}

# Функция для проверки зависимостей
check_dependencies() {
    log "Проверка зависимостей..."
    
    # Проверка наличия docker
    if ! command -v docker > /dev/null; then
        log "Ошибка: Docker не установлен"
        exit 1
    fi
    
    # Проверка наличия curl
    if ! command -v curl > /dev/null; then
        log "Ошибка: curl не установлен"
        exit 1
    fi
    
    # Проверка наличия bc
    if ! command -v bc > /dev/null; then
        log "Ошибка: bc не установлен"
        exit 1
    fi
    
    # Проверка наличия jq
    if ! command -v jq > /dev/null; then
        log "Ошибка: jq не установлен"
        exit 1
    fi
    
    # Проверка наличия Python
    if ! command -v python3 > /dev/null; then
        log "Ошибка: Python3 не установлен"
        exit 1
    fi
    
    # Проверка прав доступа к Docker
    if ! docker info > /dev/null 2>&1; then
        log "Ошибка: Недостаточно прав для работы с Docker"
        exit 1
    fi
    
    log "Все зависимости установлены"
}

# Функция для сборки Docker-образа
build_image() {
    log "Сборка Docker-образа..."
    docker build -t $IMAGE_NAME -f benchmark-suites/bun/cold-start/Dockerfile .
    log "Docker-образ собран успешно"
}

# Функция для извлечения версии Bun
get_bun_version() {
    local version=$(docker run --rm $IMAGE_NAME bun --version | tr -d '\n\r')
    log "Определена версия Bun: $version"
    echo "$version"
}

# Функция для создания директории результатов
create_results_dir() {
    log "Создание директории для результатов..."
    mkdir -p results/cold-start
    log "Директория создана"
}

# Функция для инициализации файла результатов
init_results_file() {
    local version=$1
    local system_info=$(get_system_info)
    log "Инициализация файла результатов: $RESULTS_FILE"
    
    # Создаем начальную структуру JSON
    cat > $RESULTS_FILE << EOF
{
  "runtime": "bun",
  "version": "${version}",
  "host_system": ${system_info},
  "iterations": []
}
EOF
    log "Файл результатов инициализирован"
}

# Функция для запуска контейнера и измерения времени запуска
run_benchmark_iteration() {
    local iteration=$1
    local bun_version=$2
    log "Запуск итерации $iteration..."
    
    # Создаем уникальное имя контейнера для каждой итерации
    local container_name="${CONTAINER_NAME_BASE}-$(date +%s)"
    
    # Удаляем предыдущий контейнер, если он существует
    docker ps -a | grep $container_name > /dev/null 2>&1 && docker rm -f $container_name > /dev/null 2>&1
    
    # Запускаем контейнер и записываем время начала (T0)
    local start_time=$(python3 -c "import time; print(int(time.time() * 1000))")
    log "T0: $start_time мс"
    
    # Запускаем контейнер и сохраняем логи
    docker run --name $container_name -d -p $PORT:3000 $IMAGE_NAME > /dev/null
    
    # Ожидаем сигнала готовности от сервера (T1)
    local ready_time=""
    local wait_seconds=0
    
    while [ -z "$ready_time" ] && [ $(echo "$wait_seconds < $MAX_WAIT_TIME" | bc -l) -eq 1 ]; do
        # Извлекаем временную метку готовности из логов
        ready_time=$(docker logs $container_name 2>&1 | grep "READY_TIMESTAMP:" | head -n 1 | sed 's/READY_TIMESTAMP://')
        
        if [ -z "$ready_time" ]; then
            sleep 0.1
            wait_seconds=$(echo "$wait_seconds + 0.1" | bc -l)
        fi
    done
    
    if [ -z "$ready_time" ]; then
        log "Ошибка: Превышено время ожидания готовности сервера"
        docker rm -f $container_name > /dev/null 2>&1 || true
        return 1
    fi
    
    log "T1: $ready_time мс"
    
    # Проверяем доступность сервера перед отправкой запроса
    local endpoint="http://localhost:$PORT"
    local request_successful=false
    local request_time=""
    wait_seconds=0
    
    while [ "$request_successful" = false ] && [ $(echo "$wait_seconds < $MAX_WAIT_TIME" | bc -l) -eq 1 ]; do
        # Отправляем HTTP-запрос и замеряем время (T2)
        if curl -s $endpoint -o /dev/null; then
            request_time=$(python3 -c "import time; print(int(time.time() * 1000))")
            request_successful=true
        else
            sleep 0.1
            wait_seconds=$(echo "$wait_seconds + 0.1" | bc -l)
        fi
    done
    
    if [ "$request_successful" = false ]; then
        log "Ошибка: Сервер не отвечает на HTTP-запросы"
        docker rm -f $container_name > /dev/null 2>&1 || true
        return 1
    fi
    
    log "T2: $request_time мс"
    
    # Вычисляем разницы времени
    local startup_time=$((ready_time - start_time))
    local first_request_time=$((request_time - ready_time))
    local total_time=$((request_time - start_time))
    
    log "Время запуска рантайма (T1-T0): $startup_time мс"
    log "Время первого запроса (T2-T1): $first_request_time мс"
    log "Общее время холодного старта (T2-T0): $total_time мс"
    
    # Сохраняем результаты
    STARTUP_TIMES[$iteration]=$startup_time
    FIRST_REQUEST_TIMES[$iteration]=$first_request_time
    TOTAL_TIMES[$iteration]=$total_time
    
    # Останавливаем и удаляем контейнер
    docker stop $container_name > /dev/null
    docker rm $container_name > /dev/null
    
    # Добавляем результаты в JSON
    local tmp_file=$(mktemp)
    jq --argjson new_iteration "{
        \"iteration\": $iteration,
        \"startup_time_ms\": $startup_time,
        \"first_request_time_ms\": $first_request_time,
        \"total_cold_start_time_ms\": $total_time
    }" '.iterations += [$new_iteration]' $RESULTS_FILE > $tmp_file 2>/dev/null || {
        log "Предупреждение: Ошибка при добавлении итерации в JSON. Создаю новый файл."
        cat > $RESULTS_FILE << EOF
{
  "runtime": "bun",
  "version": "$bun_version",
  "iterations": [
    {
      "iteration": $iteration,
      "startup_time_ms": $startup_time,
      "first_request_time_ms": $first_request_time,
      "total_cold_start_time_ms": $total_time
    }
  ]
}
EOF
    }
    
    if [ -f "$tmp_file" ] && [ -s "$tmp_file" ]; then
        mv $tmp_file $RESULTS_FILE
    fi
    
    log "Итерация $iteration завершена успешно"
    return 0
}

# Функция для расчета статистики
calculate_statistics() {
    log "Формирование итоговых результатов..."
    
    # Получаем версию Bun напрямую для JSON
    local bun_version=$(docker run --rm $IMAGE_NAME bun --version | tr -d '\n\r')
    log "Определена версия Bun для результатов: $bun_version"
    
    # Получаем информацию о системе хоста
    local system_info=$(get_system_info)
    
    # Добавляем результаты в JSON файл
    cat > $RESULTS_FILE << EOF
{
  "runtime": "bun",
  "version": "${bun_version}",
  "host_system": ${system_info},
  "iterations": [
EOF

    # Вручную добавляем каждую итерацию
    for ((i=1; i<=$ITERATIONS; i++)); do
        cat >> $RESULTS_FILE << EOF
    {
      "iteration": $i,
      "startup_time_ms": ${STARTUP_TIMES[$i]},
      "first_request_time_ms": ${FIRST_REQUEST_TIMES[$i]},
      "total_cold_start_time_ms": ${TOTAL_TIMES[$i]}
    }$(if [ $i -lt $ITERATIONS ]; then echo ","; fi)
EOF
    done

    # Закрываем JSON структуру
    cat >> $RESULTS_FILE << EOF
  ]
}
EOF
    
    log "Результаты сохранены в файл: $RESULTS_FILE"
}

# Главная функция
main() {
    log "=== Начало тестирования холодного старта Bun v$SCRIPT_VERSION ==="
    log "Количество итераций: $ITERATIONS"
    
    # Проверяем зависимости
    check_dependencies
    
    # Очищаем ресурсы перед началом
    cleanup
    
    # Создаем директорию для результатов
    create_results_dir
    
    # Собираем Docker-образ
    build_image
    
    # Получаем версию Bun
    local bun_version=$(get_bun_version)
    
    # Инициализируем файл результатов
    init_results_file "$bun_version"
    
    # Выполняем тестирование
    local failed_iterations=0
    
    for ((i=1; i<=$ITERATIONS; i++)); do
        log "===== Итерация $i из $ITERATIONS ====="
        if ! run_benchmark_iteration $i "$bun_version"; then
            log "Итерация $i завершилась с ошибкой"
            failed_iterations=$((failed_iterations + 1))
            
            # Если 3 итерации подряд завершились с ошибкой, прекращаем тестирование
            if [ $failed_iterations -ge 3 ]; then
                log "Три итерации подряд завершились с ошибкой. Прекращаем тестирование."
                exit 1
            fi
        else
            failed_iterations=0
        fi
    done
    
    # Рассчитываем статистику
    calculate_statistics
    
    log "=== Тестирование холодного старта Bun завершено ==="
    log "Результаты сохранены в файл: $RESULTS_FILE"
}

# Запускаем главную функцию
main 