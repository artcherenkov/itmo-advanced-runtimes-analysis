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

# Параметры запуска по умолчанию: число Фибоначчи, тип реализации (recursive/iterative), итерации
ARG FIB_N=40
ARG FIB_IMPL=recursive
ARG ITERATIONS=30

# Использование аргументов в переменных окружения
ENV FIB_N=$FIB_N
ENV FIB_IMPL=$FIB_IMPL
ENV ITERATIONS=$ITERATIONS

# Запуск бенчмарка Фибоначчи с параметрами
# Добавляем необходимые разрешения для Deno
CMD ["sh", "-c", "deno run --allow-read --allow-write --allow-env --allow-hrtime ./benchmark-suites/deno/fibonacci/index.js $FIB_N $FIB_IMPL $ITERATIONS"] 