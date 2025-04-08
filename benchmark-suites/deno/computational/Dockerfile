FROM denoland/deno:latest

WORKDIR /app

# Установка переменной окружения для обозначения контейнера
ENV CONTAINER=true

# Копирование всех файлов бенчмарка
COPY ./benchmark-suites/metrics-interface.mjs ./benchmark-suites/
COPY ./benchmark-suites/deno/computational ./benchmark-suites/deno/computational

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
  deno run --allow-hrtime --allow-read --allow-write --allow-env ./benchmark-suites/deno/computational/fibonacci.js; \
elif [ \"$BENCHMARK_TYPE\" = \"sorting\" ]; then \
  deno run --allow-hrtime --allow-read --allow-write --allow-env ./benchmark-suites/deno/computational/sorting.js; \
elif [ \"$BENCHMARK_TYPE\" = \"matrix\" ]; then \
  deno run --allow-hrtime --allow-read --allow-write --allow-env ./benchmark-suites/deno/computational/matrix.js; \
elif [ \"$BENCHMARK_TYPE\" = \"json\" ]; then \
  deno run --allow-hrtime --allow-read --allow-write --allow-env ./benchmark-suites/deno/computational/json.js; \
else \
  echo \"Неизвестный тип бенчмарка: $BENCHMARK_TYPE\"; \
  exit 1; \
fi"] 