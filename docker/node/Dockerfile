FROM node:20

WORKDIR /app

# Установка необходимых зависимостей для wrk
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка wrk
RUN git clone https://github.com/wg/wrk.git \
    && cd wrk \
    && make \
    && cp wrk /usr/local/bin \
    && cd .. \
    && rm -rf wrk

# Установка переменной окружения для обозначения контейнера
ENV CONTAINER=true

# Копирование всех файлов бенчмарка
COPY ./benchmark-suites/metrics-interface.mjs ./benchmark-suites/
COPY ./benchmark-suites/node ./benchmark-suites/node

# Создание директории для результатов
RUN mkdir -p /app/results

# Включаем принудительную сборку мусора
ENV NODE_OPTIONS="--expose-gc"

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

# Параметры для HTTP нагрузочного тестирования
ENV PORT=3030
ENV WRK_THREADS=4
ENV WRK_CONNECTIONS=100
ENV WRK_DURATION=30s

# Переменная указывающая какой тест запускать
ENV BENCHMARK_TYPE=fibonacci

# Запуск бенчмарка в зависимости от типа
CMD ["sh", "-c", "\
if [ \"$BENCHMARK_TYPE\" = \"fibonacci\" ]; then \
  node ./benchmark-suites/node/fibonacci/index.mjs; \
elif [ \"$BENCHMARK_TYPE\" = \"sorting\" ]; then \
  node ./benchmark-suites/node/sorting/index.mjs; \
elif [ \"$BENCHMARK_TYPE\" = \"matrix\" ]; then \
  node ./benchmark-suites/node/matrix/index.mjs; \
elif [ \"$BENCHMARK_TYPE\" = \"json\" ]; then \
  node ./benchmark-suites/node/json/index.mjs; \
elif [ \"$BENCHMARK_TYPE\" = \"http\" ]; then \
  node ./benchmark-suites/node/crud-http/index.mjs; \
else \
  echo \"Неизвестный тип бенчмарка: $BENCHMARK_TYPE\"; \
  exit 1; \
fi"] 