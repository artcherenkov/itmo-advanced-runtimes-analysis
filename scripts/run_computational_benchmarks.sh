#!/bin/bash

# Скрипт для последовательного запуска вычислительных бенчмарков 
# для трех JavaScript-сред выполнения: Node.js, Deno и Bun

# Цвета для форматирования вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Вывод справки
function show_help {
  echo "Использование: $0 [options]"
  echo "Опции:"
  echo "  -a, --all            Запустить все вычислительные тесты для всех сред выполнения"
  echo "  -t, --test TEST      Запустить только указанный тест (fibonacci, sorting, matrix, json)"
  echo "  -r, --runtime RUNTIME Запустить тесты только для указанной среды выполнения (node, deno, bun)"
  echo "  -i, --iterations NUM Количество итераций для тестов (по умолчанию 30)"
  echo "  -h, --help           Вывести эту справку"
  echo "Примеры:"
  echo "  $0 --all             Запустить все вычислительные тесты для всех сред выполнения"
  echo "  $0 -t fibonacci      Запустить тест Фибоначчи для всех сред выполнения"
  echo "  $0 -r node -t sorting Запустить тест сортировки только для Node.js"
  echo "  $0 -t matrix -i 50   Запустить тест умножения матриц с 50 итерациями"
  exit 0
}

# Если нет аргументов, показываем справку
if [ $# -eq 0 ]; then
  show_help
fi

# Парсинг аргументов
RUN_ALL=false
TEST=""
RUNTIME=""
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
    -r|--runtime)
      RUNTIME="$2"
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

if [ "$RUNTIME" != "" ] && [ "$RUNTIME" != "node" ] && [ "$RUNTIME" != "deno" ] && [ "$RUNTIME" != "bun" ]; then
  echo "Ошибка: Среда выполнения должна быть одной из: node, deno, bun"
  exit 1
fi

# Формируем массив сред выполнения для запуска
RUNTIMES_TO_RUN=()

if [ "$RUNTIME" != "" ]; then
  # Конкретная среда выполнения
  RUNTIMES_TO_RUN=("$RUNTIME")
else
  # Если ничего не выбрано, запускаем для всех сред
  RUNTIMES_TO_RUN=("node" "deno" "bun")
fi

# Составляем аргументы для запуска скриптов
ARGS=""

if [ "$RUN_ALL" = true ]; then
  ARGS="--all"
elif [ "$TEST" != "" ]; then
  ARGS="-t $TEST"
else
  ARGS="--all"
fi

if [ "$ITERATIONS" != "30" ]; then
  ARGS="$ARGS -i $ITERATIONS"
fi

# Показываем список сред выполнения, которые будут запущены
echo -e "${YELLOW}Будут последовательно выполнены тесты для следующих сред выполнения:${NC}"
for runtime in "${RUNTIMES_TO_RUN[@]}"; do
  echo "- $runtime"
done

if [ "$TEST" != "" ]; then
  echo -e "Будет выполнен тест: ${BLUE}$TEST${NC}"
else
  echo -e "Будут выполнены все доступные тесты"
fi

echo "Количество итераций для каждого теста: $ITERATIONS"
echo ""

# Переходим в корневую директорию проекта
cd "$(dirname "$0")/.."

# Подготовка к запуску тестов
total_runtimes=${#RUNTIMES_TO_RUN[@]}
successful_runtimes=0
failed_runtimes=0
start_time=$(date +%s)

# Последовательный запуск для каждой среды выполнения
for ((i=0; i<total_runtimes; i++)); do
  runtime="${RUNTIMES_TO_RUN[$i]}"
  echo -e "${BLUE}=== [$((i+1))/$total_runtimes] Запуск тестов для среды выполнения: $runtime ===${NC}"
  
  # Формируем путь к скрипту запуска тестов
  benchmark_script="./benchmark-suites/$runtime/computational/run_computational_benchmarks.sh"
  
  # Проверяем существование скрипта
  if [ ! -f "$benchmark_script" ]; then
    echo -e "${RED}Ошибка: Скрипт $benchmark_script не найден${NC}"
    failed_runtimes=$((failed_runtimes+1))
    continue
  fi
  
  # Запускаем скрипт бенчмарков
  echo "Выполнение команды: $benchmark_script $ARGS"
  bash "$benchmark_script" $ARGS
  
  # Проверяем результат
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Тесты для $runtime успешно завершены${NC}"
    successful_runtimes=$((successful_runtimes+1))
  else
    echo -e "${RED}Ошибка при выполнении тестов для $runtime${NC}"
    failed_runtimes=$((failed_runtimes+1))
  fi
  
  # Небольшая пауза между запусками разных сред выполнения
  if [ $i -lt $((total_runtimes-1)) ]; then
    echo "Пауза перед запуском следующей среды выполнения (10 секунд)..."
    sleep 10
  fi
done

# Выводим итоговую статистику
end_time=$(date +%s)
duration=$((end_time-start_time))
minutes=$((duration/60))
seconds=$((duration%60))

echo -e "\n${GREEN}=== Выполнение всех тестов завершено ===${NC}"
echo -e "Всего запущено сред выполнения: ${BLUE}$total_runtimes${NC}"
echo -e "Успешно выполнено: ${GREEN}$successful_runtimes${NC}"
if [ $failed_runtimes -gt 0 ]; then
  echo -e "Завершено с ошибками: ${RED}$failed_runtimes${NC}"
fi
echo -e "Общее время выполнения: ${BLUE}${minutes}m ${seconds}s${NC}"
echo -e "Результаты сохранены в директории: ${YELLOW}./results/computational${NC}"

if [ $failed_runtimes -eq 0 ]; then
  echo -e "\n${GREEN}Все тесты успешно выполнены!${NC}"
else
  echo -e "\n${RED}Некоторые тесты завершились с ошибками.${NC}"
  echo -e "Проверьте вывод выше для получения подробной информации."
fi

# Делаем скрипт исполняемым
chmod +x "$0" 