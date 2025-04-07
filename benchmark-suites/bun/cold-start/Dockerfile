FROM oven/bun:latest

WORKDIR /app

# Копирование серверного файла
COPY ./benchmark-suites/bun/cold-start/server.js .

# Открываем порт для HTTP-сервера
EXPOSE 3000

# Запускаем сервер
CMD ["bun", "server.js"] 