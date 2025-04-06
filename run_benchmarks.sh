#!/bin/bash

# Проверяем наличие папки для результатов
if [ ! -d "./results" ]; then
  mkdir -p ./results
  echo "Создана директория для результатов: ./results"
fi

# Вывод справки
function show_help {
  echo "Использование: $0 [options]"
  echo "Опции:"
  echo "  -a, --all            Запустить все тесты"
  echo "  -r, --runtime RUNTIME  Запустить тесты только для указанного рантайма (node, deno, bun)"
  echo "  -t, --test TEST      Запустить только указанный тест (fibonacci, sorting, matrix, json, http)"
  echo "  -h, --help           Вывести эту справку"
  echo "Примеры:"
  echo "  $0 --all             Запустить все тесты для всех рантаймов"
  echo "  $0 -r node -t fibonacci  Запустить тест Фибоначчи только для Node.js"
  exit 0
}

# Если нет аргументов, показываем справку
if [ $# -eq 0 ]; then
  show_help
fi

# Парсинг аргументов
RUN_ALL=false
RUNTIME=""
TEST=""

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -a|--all)
      RUN_ALL=true
      shift
      ;;
    -r|--runtime)
      RUNTIME="$2"
      shift
      shift
      ;;
    -t|--test)
      TEST="$2"
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
if [ "$RUNTIME" != "" ] && [ "$RUNTIME" != "node" ] && [ "$RUNTIME" != "deno" ] && [ "$RUNTIME" != "bun" ]; then
  echo "Ошибка: Рантайм должен быть одним из: node, deno, bun"
  exit 1
fi

if [ "$TEST" != "" ] && [ "$TEST" != "fibonacci" ] && [ "$TEST" != "sorting" ] && [ "$TEST" != "matrix" ] && [ "$TEST" != "json" ] && [ "$TEST" != "http" ]; then
  echo "Ошибка: Тест должен быть одним из: fibonacci, sorting, matrix, json, http"
  exit 1
fi

# Функция для запуска одного теста и ожидания завершения
run_single_test() {
  local service="$1"
  echo -e "\n\033[1;34m=== Запуск теста: $service ===\033[0m"
  
  # Запускаем сервис и ожидаем его завершения
  docker compose up --build --abort-on-container-exit "$service"
  
  # Проверяем статус завершения
  local exit_code=$?
  if [ $exit_code -ne 0 ]; then
    echo -e "\033[1;31mОшибка при выполнении теста $service (код $exit_code)\033[0m"
  else
    echo -e "\033[1;32mТест $service успешно завершен\033[0m"
  fi
  
  # Удаляем созданные контейнеры
  docker compose rm -f "$service" >/dev/null 2>&1
  
  return $exit_code
}

# Формируем массив сервисов для запуска
SERVICES=()

if [ "$RUN_ALL" = true ]; then
  # Все комбинации рантаймов и тестов
  RUNTIMES=("node" "deno" "bun")
  TESTS=("fibonacci" "sorting" "matrix" "json" "http")
  
  for rt in "${RUNTIMES[@]}"; do
    for tst in "${TESTS[@]}"; do
      # Пропускаем комбинации http-тестов для deno и bun, если они не реализованы
      if [ "$tst" = "http" ] && [ "$rt" != "node" ]; then
        echo "Пропускаем $rt"_"$tst (не реализовано)"
        continue
      fi
      SERVICES+=("${rt}_${tst}")
    done
  done
elif [ "$RUNTIME" != "" ] && [ "$TEST" != "" ]; then
  # Конкретный тест для конкретного рантайма
  # Проверяем, доступен ли HTTP тест для выбранного рантайма
  if [ "$TEST" = "http" ] && [ "$RUNTIME" != "node" ]; then
    echo "Ошибка: HTTP тест доступен только для Node.js"
    exit 1
  fi
  SERVICES+=("${RUNTIME}_${TEST}")
elif [ "$RUNTIME" != "" ]; then
  # Все тесты для конкретного рантайма
  TESTS=("fibonacci" "sorting" "matrix" "json")
  
  # Добавляем HTTP тест только для Node.js
  if [ "$RUNTIME" = "node" ]; then
    TESTS+=("http")
  fi
  
  for tst in "${TESTS[@]}"; do
    SERVICES+=("${RUNTIME}_${tst}")
  done
elif [ "$TEST" != "" ]; then
  # Конкретный тест для всех рантаймов
  if [ "$TEST" = "http" ]; then
    # HTTP тест доступен только для Node.js
    SERVICES+=("node_${TEST}")
  else
    SERVICES+=("node_${TEST}" "deno_${TEST}" "bun_${TEST}")
  fi
else
  # Если ничего не выбрано, запускаем всё
  RUNTIMES=("node" "deno" "bun")
  TESTS=("fibonacci" "sorting" "matrix" "json")
  
  for rt in "${RUNTIMES[@]}"; do
    for tst in "${TESTS[@]}"; do
      SERVICES+=("${rt}_${tst}")
    done
  done
  
  # Добавляем HTTP тест только для Node.js
  SERVICES+=("node_http")
fi

# Показываем список тестов, которые будут запущены
echo -e "\033[1;33mБудут последовательно выполнены следующие тесты:\033[0m"
for service in "${SERVICES[@]}"; do
  echo "- $service"
done
echo ""

# Подготовка к запуску тестов
total_tests=${#SERVICES[@]}
successful_tests=0
failed_tests=0
start_time=$(date +%s)

# Последовательный запуск каждого теста
for ((i=0; i<total_tests; i++)); do
  service="${SERVICES[$i]}"
  echo -e "\033[1;36mПрогресс: [$(($i+1))/$total_tests] Запуск $service\033[0m"
  
  # Запускаем тест
  run_single_test "$service"
  
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
echo -e "Результаты сохранены в директории: \033[1;33m./results\033[0m"

if [ $failed_tests -eq 0 ]; then
  echo -e "\n\033[1;32mВсе тесты успешно выполнены!\033[0m"
  echo -e "Для анализа результатов выполните: \033[1;36m./analyze-results.js\033[0m"
else
  echo -e "\n\033[1;31mНекоторые тесты завершились с ошибками.\033[0m"
  echo -e "Проверьте вывод выше для получения подробной информации."
fi 