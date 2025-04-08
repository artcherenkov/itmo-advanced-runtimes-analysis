#!/bin/bash

# Скрипт для запуска вычислительных тестов Bun
# Автоматически запускает выбранные тесты для Bun:
# - fibonacci: тест алгоритма Фибоначчи
# - sorting: тест алгоритмов сортировки
# - matrix: тест умножения матриц
# - json: тест парсинга и сериализации JSON

# Проверяем наличие папки для результатов
if [ ! -d "./results/computational" ]; then
  mkdir -p ./results/computational
  echo "Создана директория для результатов: ./results/computational"
fi

# Вывод справки
function show_help {
  echo "Использование: $0 [options]"
  echo "Опции:"
  echo "  -a, --all            Запустить все вычислительные тесты для Bun"
  echo "  -t, --test TEST      Запустить только указанный тест (fibonacci, sorting, matrix, json)"
  echo "  -i, --iterations NUM Количество итераций для тестов (по умолчанию 30)"
  echo "  -h, --help           Вывести эту справку"
  echo "Примеры:"
  echo "  $0 --all             Запустить все вычислительные тесты для Bun"
  echo "  $0 -t fibonacci      Запустить тест Фибоначчи для Bun"
  echo "  $0 -t sorting -i 50  Запустить тест сортировки с 50 итерациями"
  exit 0
}

# Если нет аргументов, показываем справку
if [ $# -eq 0 ]; then
  show_help
fi

# Парсинг аргументов
RUN_ALL=false
TEST=""
ITERATIONS=30

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -a|--all)
      RUN_ALL=true
      shift
      ;;
    -t|--test)
      TEST="$2"
      shift
      shift
      ;;
    -i|--iterations)
      ITERATIONS="$2"
      shift
      shift
      ;;
    -h|--help)
      show_help
      ;;
    *)
      echo "Неизвестная опция: $1"
      show_help
      ;;
  esac
done

# Проверяем корректность аргументов
if [ "$TEST" != "" ] && [ "$TEST" != "fibonacci" ] && [ "$TEST" != "sorting" ] && [ "$TEST" != "matrix" ] && [ "$TEST" != "json" ]; then
  echo "Ошибка: Тест должен быть одним из: fibonacci, sorting, matrix, json"
  exit 1
fi

# Устанавливаем переменные для Docker
IMAGE_NAME="bun-computational-benchmark"
CONTAINER_NAME_BASE="bun-computational-benchmark"

# Очистка ресурсов при выходе
trap cleanup EXIT INT TERM

# Функция для очистки ресурсов
cleanup() {
  echo "Очистка ресурсов..."
  # Останавливаем и удаляем все контейнеры с указанным именем
  docker ps -a | grep $CONTAINER_NAME_BASE | awk '{print $1}' | xargs -r docker rm -f > /dev/null 2>&1 || true
  echo "Очистка завершена"
}

# Функция для запуска одного теста
run_single_test() {
  local test_type="$1"
  local container_name="${CONTAINER_NAME_BASE}-${test_type}-$(date +%s)"
  
  echo -e "\n\033[1;34m=== Запуск теста: bun_${test_type} ===\033[0m"
  
  # Собираем Docker-образ
  echo "Сборка образа для теста $test_type..."
  docker build -t $IMAGE_NAME -f ./benchmark-suites/bun/computational/Dockerfile .
  
  echo "Запуск контейнера для теста $test_type..."
  # Запускаем контейнер с указанным тестом
  docker run --name $container_name \
    --env BENCHMARK_TYPE=$test_type \
    --env ITERATIONS=$ITERATIONS \
    $IMAGE_NAME
  
  # Проверяем статус завершения
  local exit_code=$?
  if [ $exit_code -ne 0 ]; then
    echo -e "\033[1;31mОшибка при выполнении теста bun_${test_type} (код $exit_code)\033[0m"
  else
    echo -e "\033[1;32mТест bun_${test_type} успешно завершен\033[0m"
  fi
  
  # Копируем результаты из контейнера
  docker cp $container_name:/app/results/. ./results/
  
  # Удаляем контейнер
  docker rm $container_name > /dev/null 2>&1
  
  return $exit_code
}

# Формируем массив тестов для запуска
TESTS_TO_RUN=()

if [ "$RUN_ALL" = true ]; then
  # Все тесты для Bun
  TESTS_TO_RUN=("fibonacci" "sorting" "matrix" "json")
elif [ "$TEST" != "" ]; then
  # Конкретный тест
  TESTS_TO_RUN=("$TEST")
else
  # Если ничего не выбрано, запускаем всё
  TESTS_TO_RUN=("fibonacci" "sorting" "matrix" "json")
fi

# Показываем список тестов, которые будут запущены
echo -e "\033[1;33mБудут последовательно выполнены следующие тесты для Bun:\033[0m"
for test in "${TESTS_TO_RUN[@]}"; do
  echo "- $test"
done
echo "Количество итераций для каждого теста: $ITERATIONS"
echo ""

# Подготовка к запуску тестов
total_tests=${#TESTS_TO_RUN[@]}
successful_tests=0
failed_tests=0
start_time=$(date +%s)

# Последовательный запуск каждого теста
for ((i=0; i<total_tests; i++)); do
  test="${TESTS_TO_RUN[$i]}"
  echo -e "\033[1;36mПрогресс: [$(($i+1))/$total_tests] Запуск теста $test\033[0m"
  
  # Запускаем тест
  run_single_test "$test"
  
  # Проверяем результат
  if [ $? -eq 0 ]; then
    successful_tests=$((successful_tests+1))
  else
    failed_tests=$((failed_tests+1))
  fi
  
  # Небольшая пауза между тестами для стабилизации системы
  if [ $i -lt $((total_tests-1)) ]; then
    echo "Пауза перед следующим тестом (5 секунд)..."
    sleep 5
  fi
done

# Выводим итоговую статистику
end_time=$(date +%s)
duration=$((end_time-start_time))
minutes=$((duration/60))
seconds=$((duration%60))

echo -e "\n\033[1;32m=== Выполнение тестов завершено ===\033[0m"
echo -e "Всего запущено тестов: \033[1;36m$total_tests\033[0m"
echo -e "Успешно выполнено: \033[1;32m$successful_tests\033[0m"
if [ $failed_tests -gt 0 ]; then
  echo -e "Завершено с ошибками: \033[1;31m$failed_tests\033[0m"
fi
echo -e "Общее время выполнения: \033[1;36m${minutes}m ${seconds}s\033[0m"
echo -e "Результаты сохранены в директории: \033[1;33m./results/computational\033[0m"

if [ $failed_tests -eq 0 ]; then
  echo -e "\n\033[1;32mВсе тесты успешно выполнены!\033[0m"
else
  echo -e "\n\033[1;31mНекоторые тесты завершились с ошибками.\033[0m"
  echo -e "Проверьте вывод выше для получения подробной информации."
fi 