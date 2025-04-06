FROM denoland/deno:latest

WORKDIR /app

# Установка переменной окружения для обозначения контейнера
ENV CONTAINER=true

# Копирование всех файлов бенчмарка
COPY ./benchmark-suites/metrics-interface.mjs ./benchmark-suites/
COPY ./benchmark-suites/deno ./benchmark-suites/deno

# Создание директории для результатов
RUN mkdir -p /app/results
# Установка прав на запись в директорию результатов
RUN chmod -R 777 /app/results

# Монтирование директории результатов
VOLUME ["/app/results"]

# Предварительное кэширование модулей для более быстрого выполнения
RUN deno cache --reload ./benchmark-suites/metrics-interface.mjs
RUN deno cache --reload ./benchmark-suites/deno/utils/metrics.js
RUN deno cache --reload ./benchmark-suites/deno/fibonacci/index.js
RUN deno cache --reload ./benchmark-suites/deno/sorting/index.js
RUN deno cache --reload ./benchmark-suites/deno/matrix/index.js
RUN deno cache --reload ./benchmark-suites/deno/json/index.js

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
  deno run --allow-read --allow-write --allow-env --allow-hrtime ./benchmark-suites/deno/fibonacci/index.js $FIB_N $FIB_IMPL $ITERATIONS; \
elif [ \"$BENCHMARK_TYPE\" = \"sorting\" ]; then \
  deno run --allow-read --allow-write --allow-env --allow-hrtime ./benchmark-suites/deno/sorting/index.js $ARRAY_SIZE $SORT_ALGORITHM $ITERATIONS; \
elif [ \"$BENCHMARK_TYPE\" = \"matrix\" ]; then \
  deno run --allow-read --allow-write --allow-env --allow-hrtime ./benchmark-suites/deno/matrix/index.js $MATRIX_SIZE $MATRIX_ALGORITHM $ITERATIONS; \
elif [ \"$BENCHMARK_TYPE\" = \"json\" ]; then \
  deno run --allow-read --allow-write --allow-env --allow-hrtime ./benchmark-suites/deno/json/index.js $JSON_OBJECT_SIZE $JSON_OPERATION $ITERATIONS; \
else \
  echo \"Неизвестный тип бенчмарка: $BENCHMARK_TYPE\"; \
  exit 1; \
fi"] 