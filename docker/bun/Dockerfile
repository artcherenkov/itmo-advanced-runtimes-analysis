FROM oven/bun:latest

WORKDIR /app

# Установка переменной окружения для обозначения контейнера
ENV CONTAINER=true

# Копирование всех файлов бенчмарка
COPY ./benchmark-suites/metrics-interface.mjs ./benchmark-suites/
COPY ./benchmark-suites/bun ./benchmark-suites/bun

# Создание директории для результатов
RUN mkdir -p /app/results

# Тип бенчмарка по умолчанию - fibonacci
ENV BENCHMARK_TYPE=fibonacci

# Параметры запуска для бенчмарка Fibonacci по умолчанию
ENV FIB_N=40
ENV FIB_IMPL=recursive
ENV ITERATIONS=30

# Параметры запуска для бенчмарка Sorting по умолчанию
ENV ARRAY_SIZE=10000
ENV SORT_ALGORITHM=quicksort

# Параметры запуска для бенчмарка Matrix по умолчанию
ENV MATRIX_SIZE=250
ENV MATRIX_ALGORITHM=naive

# Параметры запуска для бенчмарка JSON по умолчанию
ENV JSON_OBJECT_SIZE=1000
ENV JSON_OPERATION=parse-stringify

# Скрипт для запуска нужного бенчмарка в зависимости от BENCHMARK_TYPE
CMD if [ "$BENCHMARK_TYPE" = "fibonacci" ]; then \
      bun ./benchmark-suites/bun/fibonacci/index.js $FIB_N $FIB_IMPL $ITERATIONS; \
    elif [ "$BENCHMARK_TYPE" = "sorting" ]; then \
      bun ./benchmark-suites/bun/sorting/index.js $ARRAY_SIZE $SORT_ALGORITHM $ITERATIONS; \
    elif [ "$BENCHMARK_TYPE" = "matrix" ]; then \
      bun ./benchmark-suites/bun/matrix/index.js $MATRIX_SIZE $MATRIX_ALGORITHM $ITERATIONS; \
    elif [ "$BENCHMARK_TYPE" = "json" ]; then \
      bun ./benchmark-suites/bun/json/index.js $JSON_OBJECT_SIZE $JSON_OPERATION $ITERATIONS; \
    else \
      echo "Неизвестный тип бенчмарка: $BENCHMARK_TYPE"; \
      exit 1; \
    fi 