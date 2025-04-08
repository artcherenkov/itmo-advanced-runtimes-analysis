FROM oven/bun:latest

WORKDIR /app

# Установка переменной окружения для обозначения контейнера
ENV CONTAINER=true

# Копирование всех файлов бенчмарка
COPY ./benchmark-suites/metrics-interface.mjs ./benchmark-suites/
COPY ./benchmark-suites/bun/computational ./benchmark-suites/bun/computational

# Создание директории для результатов
RUN mkdir -p /app/results/computational

# Параметры по умолчанию для всех тестов
ENV ITERATIONS=30

# Параметры для теста Фибоначчи
ENV FIB_N=40
ENV FIB_IMPL=recursive

# Параметры для теста сортировки
ENV ARRAY_SIZE=10000
ENV SORT_ALGORITHM=quicksort

# Параметры для теста умножения матриц
ENV MATRIX_SIZE=250
ENV MATRIX_ALGORITHM=naive

# Параметры для теста JSON
ENV JSON_OBJECT_SIZE=1000
ENV JSON_OPERATION=parse-stringify

# Переменная указывающая какой тест запускать
ENV BENCHMARK_TYPE=fibonacci

# Запуск бенчмарка в зависимости от типа
CMD ["sh", "-c", "\
if [ \"$BENCHMARK_TYPE\" = \"fibonacci\" ]; then \
  bun run ./benchmark-suites/bun/computational/fibonacci.js; \
elif [ \"$BENCHMARK_TYPE\" = \"sorting\" ]; then \
  bun run ./benchmark-suites/bun/computational/sorting.js; \
elif [ \"$BENCHMARK_TYPE\" = \"matrix\" ]; then \
  bun run ./benchmark-suites/bun/computational/matrix.js; \
elif [ \"$BENCHMARK_TYPE\" = \"json\" ]; then \
  bun run ./benchmark-suites/bun/computational/json.js; \
else \
  echo \"Неизвестный тип бенчмарка: $BENCHMARK_TYPE\"; \
  exit 1; \
fi"] 