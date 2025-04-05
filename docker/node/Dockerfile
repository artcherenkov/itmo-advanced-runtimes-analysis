FROM node:20

WORKDIR /app

# Установка переменной окружения для обозначения контейнера
ENV CONTAINER=true

# Копирование всех файлов бенчмарка
COPY ./benchmark-suites/metrics-interface.js ./benchmark-suites/
COPY ./benchmark-suites/node ./benchmark-suites/node

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

# Включаем принудительную сборку мусора
ENV NODE_OPTIONS="--expose-gc"

# Запуск бенчмарка Фибоначчи с параметрами
CMD ["sh", "-c", "node ./benchmark-suites/node/fibonacci/index.js $FIB_N $FIB_IMPL $ITERATIONS"] 