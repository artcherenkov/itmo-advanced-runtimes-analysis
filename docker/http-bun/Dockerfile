FROM oven/bun:latest

WORKDIR /app

# Копирование файла сервера
COPY ./benchmark-suites/bun/http/index.js .

# Открываем порт
EXPOSE 3003

# Запуск сервера
CMD ["bun", "index.js"] 