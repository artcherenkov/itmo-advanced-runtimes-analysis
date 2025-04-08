FROM oven/bun:latest

WORKDIR /app

# Копирование файла сервера
COPY ./index.js .

# Открываем порт
EXPOSE 3103

# Запуск сервера
CMD ["bun", "index.js"] 