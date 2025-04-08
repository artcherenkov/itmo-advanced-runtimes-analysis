#!/bin/bash

# Скрипт для запуска всех бенчмарков JS-рантаймов
# Запускает:
# - Вычислительные бенчмарки (Fibonacci, сортировка, умножение матриц, JSON)
# - HTTP бенчмарки (простые HTTP-запросы)
# - Асинхронные бенчмарки (асинхронные операции)
# - Тесты холодного старта

# Цвета для форматирования вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Переменные для опций запуска
RUN_COMPUTATIONAL=false
RUN_HTTP=false
RUN_ASYNC=false
RUN_COLD_START=false
RUN_ALL=false
RUNTIMES=()
ITERATIONS=30
VERBOSE=false

# Вывод справки
function show_help {
  echo "Использование: $0 [options]"
  echo "Опции:"
  echo "  -a, --all               Запустить все тесты для всех рантаймов"
  echo "  -c, --computational     Запустить вычислительные тесты"
  echo "  -h, --http              Запустить HTTP бенчмарки"
  echo "  -s, --async             Запустить асинхронные бенчмарки"
  echo "  -d, --cold-start        Запустить тесты холодного старта"
  echo "  -r, --runtime RUNTIME   Рантайм для тестирования (node, deno, bun), можно указать несколько раз"
  echo "  -i, --iterations NUM    Количество итераций для тестов (по умолчанию 30)"
  echo "  -v, --verbose           Подробный вывод"
  echo "  --help                  Вывести эту справку"
  echo
  echo "Примеры:"
  echo "  $0 --all                Запустить все бенчмарки для всех рантаймов"
  echo "  $0 -c -h -r node        Запустить вычислительные и HTTP тесты только для Node.js"
  echo "  $0 --http --async -r bun -r deno -i 10  Запустить HTTP и асинхронные тесты для Bun и Deno с 10 итерациями"
  exit 0
}

# Если нет аргументов, показываем справку
if [ $# -eq 0 ]; then
  show_help
fi

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -a|--all)
      RUN_ALL=true
      shift
      ;;
    -c|--computational)
      RUN_COMPUTATIONAL=true
      shift
      ;;
    -h|--http)
      RUN_HTTP=true
      shift
      ;;
    -s|--async)
      RUN_ASYNC=true
      shift
      ;;
    -d|--cold-start)
      RUN_COLD_START=true
      shift
      ;;
    -r|--runtime)
      RUNTIMES+=("$2")
      shift
      shift
      ;;
    -i|--iterations)
      ITERATIONS="$2"
      shift
      shift
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      show_help
      ;;
    *)
      echo "Неизвестная опция: $1"
      show_help
      ;;
  esac
done

# Если выбрана опция --all, включаем все тесты
if [ "$RUN_ALL" = true ]; then
  RUN_COMPUTATIONAL=true
  RUN_HTTP=true
  RUN_ASYNC=true
  RUN_COLD_START=true
fi

# Если не выбран ни один тест, выводим ошибку
if [ "$RUN_COMPUTATIONAL" = false ] && [ "$RUN_HTTP" = false ] && [ "$RUN_ASYNC" = false ] && [ "$RUN_COLD_START" = false ]; then
  echo -e "${RED}Ошибка: Не выбран ни один тип тестов${NC}"
  echo "Используйте опции -c, -h, -s, -d для выбора типов тестов или -a для запуска всех тестов"
  exit 1
fi

# Если не выбран ни один рантайм, используем все
if [ ${#RUNTIMES[@]} -eq 0 ]; then
  RUNTIMES=("node" "deno" "bun")
fi

# Переходим в корневую директорию проекта
cd "$(dirname "$0")/.."

# Проверяем наличие директории для результатов
if [ ! -d "./results" ]; then
  mkdir -p "./results"
fi

# Функция для логирования с отметкой времени
log() {
  if [ "$VERBOSE" = true ] || [ "$2" = "important" ]; then
    echo -e "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
  fi
}

# Функция для запуска вычислительных тестов
run_computational_benchmarks() {
  log "${BLUE}=== Запуск вычислительных тестов ===${NC}" "important"
  
  # Формируем аргументы для запуска тестов
  ARGS="-i $ITERATIONS"
  
  # Если указаны конкретные рантаймы, добавляем их в аргументы
  if [ ${#RUNTIMES[@]} -gt 0 ]; then
    for runtime in "${RUNTIMES[@]}"; do
      log "Запуск вычислительных тестов для рантайма: $runtime" "important"
      bash ./scripts/run_computational_benchmarks.sh -r $runtime $ARGS
      if [ $? -ne 0 ]; then
        log "${RED}Ошибка при запуске вычислительных тестов для $runtime${NC}" "important"
      else
        log "${GREEN}Вычислительные тесты для $runtime завершены успешно${NC}" "important"
      fi
    done
  else
    # Запускаем для всех рантаймов
    log "Запуск вычислительных тестов для всех рантаймов" "important"
    bash ./scripts/run_computational_benchmarks.sh --all $ARGS
  fi
  
  log "${GREEN}Вычислительные тесты завершены${NC}" "important"
}

# Функция для запуска HTTP тестов
run_http_benchmarks() {
  log "${BLUE}=== Запуск HTTP тестов ===${NC}" "important"
  
  for runtime in "${RUNTIMES[@]}"; do
    log "Запуск HTTP тестов для рантайма: $runtime" "important"
    bash ./scripts/run_http_benchmarks.sh $runtime $ITERATIONS
    if [ $? -ne 0 ]; then
      log "${RED}Ошибка при запуске HTTP тестов для $runtime${NC}" "important"
    else
      log "${GREEN}HTTP тесты для $runtime завершены успешно${NC}" "important"
    fi
  done
  
  log "${GREEN}HTTP тесты завершены${NC}" "important"
}

# Функция для запуска асинхронных тестов
run_async_benchmarks() {
  log "${BLUE}=== Запуск асинхронных тестов ===${NC}" "important"
  
  for runtime in "${RUNTIMES[@]}"; do
    log "Запуск асинхронных тестов для рантайма: $runtime" "important"
    bash ./scripts/run_async_benchmarks.sh $runtime $ITERATIONS
    if [ $? -ne 0 ]; then
      log "${RED}Ошибка при запуске асинхронных тестов для $runtime${NC}" "important"
    else
      log "${GREEN}Асинхронные тесты для $runtime завершены успешно${NC}" "important"
    fi
  done
  
  log "${GREEN}Асинхронные тесты завершены${NC}" "important"
}

# Функция для запуска тестов холодного старта
run_cold_start_benchmarks() {
  log "${BLUE}=== Запуск тестов холодного старта ===${NC}" "important"
  
  for runtime in "${RUNTIMES[@]}"; do
    log "Запуск тестов холодного старта для рантайма: $runtime" "important"
    bash ./benchmark-suites/$runtime/cold-start/cold_start_benchmark.sh -i $ITERATIONS
    if [ $? -ne 0 ]; then
      log "${RED}Ошибка при запуске тестов холодного старта для $runtime${NC}" "important"
    else
      log "${GREEN}Тесты холодного старта для $runtime завершены успешно${NC}" "important"
    fi
  done
  
  log "${GREEN}Тесты холодного старта завершены${NC}" "important"
}

# Функция для отображения общей информации о запускаемых тестах
show_run_info() {
  echo -e "${BLUE}=== Конфигурация запуска бенчмарков ===${NC}"
  echo -e "Выбранные рантаймы: ${YELLOW}${RUNTIMES[*]}${NC}"
  echo -e "Количество итераций: ${YELLOW}$ITERATIONS${NC}"
  echo -e "Выбранные тесты:"
  
  if [ "$RUN_COMPUTATIONAL" = true ]; then
    echo -e "  - ${GREEN}Вычислительные тесты${NC}"
  fi
  
  if [ "$RUN_HTTP" = true ]; then
    echo -e "  - ${GREEN}HTTP тесты${NC}"
  fi
  
  if [ "$RUN_ASYNC" = true ]; then
    echo -e "  - ${GREEN}Асинхронные тесты${NC}"
  fi
  
  if [ "$RUN_COLD_START" = true ]; then
    echo -e "  - ${GREEN}Тесты холодного старта${NC}"
  fi
  
  echo ""
}

# Основная функция
main() {
  # Показываем информацию о запуске
  show_run_info
  
  # Начинаем отсчет времени
  START_TIME=$(date +%s)
  
  # Запускаем выбранные тесты
  if [ "$RUN_COMPUTATIONAL" = true ]; then
    run_computational_benchmarks
    echo ""
  fi
  
  if [ "$RUN_HTTP" = true ]; then
    run_http_benchmarks
    echo ""
  fi
  
  if [ "$RUN_ASYNC" = true ]; then
    run_async_benchmarks
    echo ""
  fi
  
  if [ "$RUN_COLD_START" = true ]; then
    run_cold_start_benchmarks
    echo ""
  fi
  
  # Завершаем отсчет времени
  END_TIME=$(date +%s)
  DURATION=$((END_TIME-START_TIME))
  
  # Выводим общую статистику
  echo -e "${BLUE}=== Сводка выполнения всех тестов ===${NC}"
  echo -e "Общее время выполнения: ${GREEN}$(($DURATION / 60)) мин $(($DURATION % 60)) сек${NC}"
  echo -e "Все результаты сохранены в директории: ${YELLOW}./results${NC}"
  echo -e "${GREEN}Тестирование завершено!${NC}"
}

# Запускаем основную функцию
main 