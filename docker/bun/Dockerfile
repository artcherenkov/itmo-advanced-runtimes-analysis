FROM oven/bun:latest

WORKDIR /app

# Установка переменной окружения для обозначения контейнера
ENV CONTAINER=true

# Копирование всех файлов бенчмарка
COPY ./benchmark-suites/metrics-interface.mjs ./benchmark-suites/
COPY ./benchmark-suites/bun ./benchmark-suites/bun

# Создание директории для результатов
RUN mkdir -p /app/results

# Параметры запуска по умолчанию: число Фибоначчи, тип реализации (recursive/iterative), итерации
ARG FIB_N=40
ARG FIB_IMPL=recursive
ARG ITERATIONS=30

# Использование аргументов в переменных окружения
ENV FIB_N=$FIB_N
ENV FIB_IMPL=$FIB_IMPL
ENV ITERATIONS=$ITERATIONS

# Запуск бенчмарка Фибоначчи с параметрами
CMD ["sh", "-c", "bun ./benchmark-suites/bun/fibonacci/index.js $FIB_N $FIB_IMPL $ITERATIONS"] 