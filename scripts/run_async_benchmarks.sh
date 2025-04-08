#!/bin/bash

# Скрипт для проведения нагрузочного тестирования асинхронных HTTP-серверов
# Использование: ./run_async_benchmarks.sh <runtime> [iterations]
# Где <runtime> может быть: node, deno или bun
# [iterations] - количество итераций тестирования (по умолчанию 1)

# Проверка количества аргументов
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo "Использование: $0 <runtime> [iterations]"
    echo "Доступные рантаймы: node, deno, bun"
    exit 1
fi

RUNTIME=$1
ITERATIONS=${2:-1}  # По умолчанию 1 итерация, если не указано иное
TIMESTAMP=$(date +%Y%m%d%H%M%S)
RESULTS_DIR="./results/async"
RESULTS_FILE="${RESULTS_DIR}/${RUNTIME}_async_${TIMESTAMP}.json"
TMP_FILE="/tmp/wrk_output.txt"

# Проверка корректности указанного рантайма
case $RUNTIME in
    "node")
        SERVICE="simple_async_node"
        PORT=3101
        ;;
    "deno")
        SERVICE="simple_async_deno"
        PORT=3102
        ;;
    "bun")
        SERVICE="simple_async_bun"
        PORT=3103
        ;;
    *)
        echo "Ошибка: Неизвестный рантайм '$RUNTIME'"
        echo "Доступные рантаймы: node, deno, bun"
        exit 1
        ;;
esac

# Создание директории для результатов, если она не существует
mkdir -p $RESULTS_DIR

echo "Запуск асинхронного HTTP-сервера на базе $RUNTIME..."
docker compose up -d $SERVICE

# Ожидание запуска сервера
echo "Ожидание запуска сервера..."
sleep 5

# Проверка доступности сервера
for i in {1..10}; do
    if curl -s http://localhost:$PORT/async-bench > /dev/null; then
        echo "Сервер запущен и отвечает."
        break
    fi
    
    if [ $i -eq 10 ]; then
        echo "Ошибка: Сервер не отвечает. Завершение тестирования."
        docker compose stop $SERVICE
        exit 1
    fi
    
    echo "Ожидание запуска сервера (попытка $i из 10)..."
    sleep 3
done

# Настройки для wrk
WRK_THREADS=4
WRK_CONNECTIONS=100
WRK_DURATION=30s
WRK_URL="http://localhost:$PORT/async-bench"

# Создание начала JSON-файла
cat > $RESULTS_FILE << EOF
{
  "runtime": "$RUNTIME",
  "timestamp": "$(date +%Y-%m-%dT%H:%M:%S)",
  "configuration": {
    "threads": $WRK_THREADS,
    "connections": $WRK_CONNECTIONS,
    "duration": "$WRK_DURATION",
    "url": "$WRK_URL",
    "iterations": $ITERATIONS
  },
  "iterations": [
EOF

SUCCESS=true
WRK_EXIT_CODE=0

# Цикл для запуска нескольких итераций тестирования
for ((i=1; i<=$ITERATIONS; i++)); do
    echo "Запуск итерации $i из $ITERATIONS..."
    
    # Запуск wrk и сохранение результатов во временный файл
    wrk -t$WRK_THREADS -c$WRK_CONNECTIONS -d$WRK_DURATION $WRK_URL > $TMP_FILE 2>&1
    CURRENT_WRK_EXIT_CODE=$?
    
    # Если есть ошибка, обновляем общий статус
    if [ $CURRENT_WRK_EXIT_CODE -ne 0 ]; then
        SUCCESS=false
        WRK_EXIT_CODE=$CURRENT_WRK_EXIT_CODE
    fi
    
    # Вывод содержимого файла для отладки
    echo "Вывод wrk (итерация $i):"
    cat $TMP_FILE
    
    # Извлечение данных с помощью awk
    # Извлечение информации о латентности (Latency)
    LATENCY_LINE=$(grep "Latency" $TMP_FILE)
    LATENCY_AVG=$(echo "$LATENCY_LINE" | awk '{print $2}')
    LATENCY_STDEV=$(echo "$LATENCY_LINE" | awk '{print $3}')
    LATENCY_MAX=$(echo "$LATENCY_LINE" | awk '{print $4}')
    
    # Извлечение информации о запросах в секунду (Req/Sec)
    REQ_SEC_LINE=$(grep "Req/Sec" $TMP_FILE)
    
    # Обработка значений с 'k' (тысячи)
    REQ_SEC_AVG_RAW=$(echo "$REQ_SEC_LINE" | awk '{print $2}')
    REQ_SEC_STDEV_RAW=$(echo "$REQ_SEC_LINE" | awk '{print $3}')
    REQ_SEC_MAX_RAW=$(echo "$REQ_SEC_LINE" | awk '{print $4}')
    
    # Функция для конвертации k (тысячи) в числовое значение
    convert_k_value() {
        local value=$1
        if [[ "$value" == *k ]]; then
            echo "$value" | sed 's/k//' | awk '{print $1 * 1000}'
        else
            echo "$value"
        fi
    }
    
    REQ_SEC_AVG=$(convert_k_value "$REQ_SEC_AVG_RAW")
    REQ_SEC_STDEV=$(convert_k_value "$REQ_SEC_STDEV_RAW")
    REQ_SEC_MAX=$(convert_k_value "$REQ_SEC_MAX_RAW")
    
    # Извлечение информации о запросах и продолжительности
    REQUESTS_LINE=$(grep "requests in" $TMP_FILE)
    TOTAL_REQUESTS=$(echo "$REQUESTS_LINE" | awk '{print $1}')
    DURATION=$(echo "$REQUESTS_LINE" | awk '{print $4}' | sed 's/s,//')
    
    # Извлечение информации о запросах в секунду
    REQUESTS_PER_SEC=$(grep "Requests/sec:" $TMP_FILE | awk '{print $2}')
    
    # Извлечение информации о скорости передачи
    TRANSFER_PER_SEC=$(grep "Transfer/sec:" $TMP_FILE | awk '{print $2}')
    
    # Проверка и задание значений по умолчанию, если данные не удалось извлечь
    if [ -z "$LATENCY_AVG" ]; then LATENCY_AVG="N/A"; fi
    if [ -z "$LATENCY_STDEV" ]; then LATENCY_STDEV="N/A"; fi
    if [ -z "$LATENCY_MAX" ]; then LATENCY_MAX="N/A"; fi
    if [ -z "$REQ_SEC_AVG" ]; then REQ_SEC_AVG=0; fi
    if [ -z "$REQ_SEC_STDEV" ]; then REQ_SEC_STDEV=0; fi
    if [ -z "$REQ_SEC_MAX" ]; then REQ_SEC_MAX=0; fi
    if [ -z "$TOTAL_REQUESTS" ]; then TOTAL_REQUESTS=0; fi
    if [ -z "$DURATION" ]; then DURATION=0; fi
    if [ -z "$REQUESTS_PER_SEC" ]; then REQUESTS_PER_SEC=0; fi
    if [ -z "$TRANSFER_PER_SEC" ]; then TRANSFER_PER_SEC="N/A"; fi
    
    echo "Извлеченные данные (итерация $i):"
    echo "Latency AVG: $LATENCY_AVG"
    echo "Latency STDEV: $LATENCY_STDEV"
    echo "Latency MAX: $LATENCY_MAX"
    echo "Req/Sec AVG: $REQ_SEC_AVG"
    echo "Req/Sec STDEV: $REQ_SEC_STDEV"
    echo "Req/Sec MAX: $REQ_SEC_MAX"
    echo "Total Requests: $TOTAL_REQUESTS"
    echo "Duration: $DURATION"
    echo "Requests/sec: $REQUESTS_PER_SEC"
    echo "Transfer/sec: $TRANSFER_PER_SEC"
    
    # Также анализируем JSON-ответ сервера для получения дополнительных метрик
    # Выполняем запрос к серверу и сохраняем ответ
    SERVER_RESPONSE=$(curl -s http://localhost:$PORT/async-bench)
    ASYNC_DURATION=$(echo $SERVER_RESPONSE | grep -o '"duration_ms":[0-9.]*' | cut -d':' -f2)
    
    # Добавление результата итерации в JSON
    if [ $i -gt 1 ]; then
        # Добавить запятую после предыдущей итерации, кроме последней
        echo "," >> $RESULTS_FILE
    fi
    
    # Запись результатов итерации в JSON
    cat >> $RESULTS_FILE << EOF
    {
      "iteration": $i,
      "timestamp": "$(date +%Y-%m-%dT%H:%M:%S)",
      "success": $([ $CURRENT_WRK_EXIT_CODE -eq 0 ] && echo "true" || echo "false"),
      "results": {
        "latency": {
          "avg": "$LATENCY_AVG",
          "stdev": "$LATENCY_STDEV",
          "max": "$LATENCY_MAX"
        },
        "requests_per_sec": {
          "avg": $REQ_SEC_AVG,
          "stdev": $REQ_SEC_STDEV,
          "max": $REQ_SEC_MAX
        },
        "summary": {
          "total_requests": $TOTAL_REQUESTS,
          "duration_seconds": $DURATION,
          "requests_per_sec": $REQUESTS_PER_SEC,
          "transfer_per_sec": "$TRANSFER_PER_SEC",
          "server_async_duration_ms": $ASYNC_DURATION
        }
      },
      "raw_output": "$(cat $TMP_FILE | sed 's/"/\\"/g' | tr '\n' ' ')",
      "server_response": $(echo $SERVER_RESPONSE | sed 's/$//')
    }
EOF

    # Небольшая пауза между итерациями для стабилизации системы
    if [ $i -lt $ITERATIONS ]; then
        echo "Ждем 5 секунд перед следующей итерацией..."
        sleep 5
    fi
done

# Завершение JSON-структуры
cat >> $RESULTS_FILE << EOF
  ],
  "success": $SUCCESS
}
EOF

echo "Результаты всех итераций сохранены в файл: $RESULTS_FILE"

# Удаление временного файла
rm -f $TMP_FILE

# Остановка сервера
echo "Остановка асинхронного HTTP-сервера..."
docker compose stop $SERVICE

exit $WRK_EXIT_CODE 