#!/bin/bash

# Скрипт для запуска всех бенчмарков через Docker на основе конфигурационного файла
set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка наличия jq
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Ошибка: jq не установлен. Установите jq для работы с JSON.${NC}"
    echo "Для установки: brew install jq (macOS) или apt-get install jq (Ubuntu)"
    exit 1
fi

# Загрузка конфигурации
CONFIG_FILE="benchmark-config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Ошибка: Файл конфигурации $CONFIG_FILE не найден.${NC}"
    exit 1
fi

# Директория для результатов
RESULTS_DIR=$(jq -r '.global.resultsPath' "$CONFIG_FILE")
mkdir -p "$RESULTS_DIR"

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}= Запуск бенчмарков через Docker    =${NC}"
echo -e "${GREEN}=====================================${NC}"

# Очистка предыдущих результатов (опционально)
read -p "Очистить предыдущие результаты? (y/n): " CLEAN_RESULTS
if [[ $CLEAN_RESULTS == "y" || $CLEAN_RESULTS == "Y" ]]; then
  echo -e "${YELLOW}Очистка директории с результатами...${NC}"
  rm -rf "$RESULTS_DIR"/*
fi

# Функция для запуска бенчмарка через Docker
run_benchmark() {
  local runtime=$1
  local experiment=$2
  local params=$3
  
  # Извлекаем параметры
  local n=$(echo "$params" | jq -r '.n')
  local implementation=$(echo "$params" | jq -r '.implementation')
  local iterations=$(echo "$params" | jq -r '.iterations')
  
  echo -e "${BLUE}===============================================${NC}"
  echo -e "${BLUE}Запуск бенчмарка ${YELLOW}$runtime: $experiment${NC}"
  echo -e "${BLUE}Параметры: n=$n, реализация=$implementation, итерации=$iterations${NC}"
  echo -e "${BLUE}===============================================${NC}"
  
  # Генерируем уникальный идентификатор для запуска (только цифры)
  local run_id=$(date +%s)
  
  # Сборка Docker-образа для соответствующего рантайма
  case $runtime in
    "node")
      echo -e "${YELLOW}Сборка Docker-образа для Node.js...${NC}"
      docker build -t js-benchmark-$runtime-$run_id -f docker/$runtime/Dockerfile \
        --build-arg FIB_N=$n \
        --build-arg FIB_IMPL=$implementation \
        --build-arg ITERATIONS=$iterations \
        .
      
      echo -e "${YELLOW}Запуск контейнера...${NC}"
      docker run --rm -v "$(pwd)/$RESULTS_DIR:/app/results" js-benchmark-$runtime-$run_id
      ;;
      
    "deno")
      echo -e "${YELLOW}Сборка Docker-образа для Deno...${NC}"
      docker build -t js-benchmark-$runtime-$run_id -f docker/$runtime/Dockerfile \
        --build-arg FIB_N=$n \
        --build-arg FIB_IMPL=$implementation \
        --build-arg ITERATIONS=$iterations \
        .
      
      echo -e "${YELLOW}Запуск контейнера...${NC}"
      docker run --rm \
        -v "$(pwd)/$RESULTS_DIR:/app/results" \
        -e RESULTS_DIR=/app/results \
        js-benchmark-$runtime-$run_id
      ;;
      
    "bun")
      echo -e "${YELLOW}Сборка Docker-образа для Bun...${NC}"
      docker build -t js-benchmark-$runtime-$run_id -f docker/$runtime/Dockerfile \
        --build-arg FIB_N=$n \
        --build-arg FIB_IMPL=$implementation \
        --build-arg ITERATIONS=$iterations \
        .
      
      echo -e "${YELLOW}Запуск контейнера...${NC}"
      docker run --rm -v "$(pwd)/$RESULTS_DIR:/app/results" js-benchmark-$runtime-$run_id
      ;;
      
    *)
      echo -e "${RED}Неизвестный рантайм: $runtime${NC}"
      return 1
      ;;
  esac
  
  echo -e "${GREEN}Бенчмарк $runtime:$experiment завершен${NC}"
}

# Проход по всем экспериментам в конфигурации
echo -e "${YELLOW}Обработка конфигурации экспериментов...${NC}"
num_experiments=$(jq '.experiments | length' "$CONFIG_FILE")

for ((i=0; i<num_experiments; i++)); do
  experiment_name=$(jq -r ".experiments[$i].name" "$CONFIG_FILE")
  runtimes=$(jq -r ".experiments[$i].runtimes[]" "$CONFIG_FILE")
  
  echo -e "${BLUE}Эксперимент: $experiment_name${NC}"
  
  # Получаем все конфигурации для эксперимента
  num_configs=$(jq ".experiments[$i].configurations | length" "$CONFIG_FILE")
  
  for ((j=0; j<num_configs; j++)); do
    parameters=$(jq -c ".experiments[$i].configurations[$j].parameters" "$CONFIG_FILE")
    
    # Запускаем эксперимент для каждого рантайма
    for runtime in $runtimes; do
      run_benchmark "$runtime" "$experiment_name" "$parameters"
    done
  done
done

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}= Все бенчмарки успешно завершены!  =${NC}"
echo -e "${GREEN}=====================================${NC}"
echo -e "Результаты доступны в директории: ${YELLOW}$RESULTS_DIR${NC}"

# Генерация краткой статистики результатов
echo -e "${BLUE}Генерация краткой статистики...${NC}"
echo -e "Запущено экспериментов: $(find "$RESULTS_DIR" -name "*.json" | wc -l)"

# Вывод средних значений времени выполнения для каждого эксперимента
echo -e "${YELLOW}Средние значения времени выполнения:${NC}"
for result in "$RESULTS_DIR"/*.json; do
  if [ -f "$result" ]; then
    runtime=$(jq -r '.runtime' "$result")
    experiment=$(jq -r '.experiment' "$result")
    mean=$(jq -r '.statistics.mean' "$result")
    mean_ms=$(echo "scale=3; $mean / 1000000" | bc)
    echo -e "${runtime}: ${experiment} = ${mean_ms} ms"
  fi
done 