FROM node:20

WORKDIR /app

# Копирование файла сервера
COPY ./benchmark-suites/node/http/index.js .

# Открываем порт
EXPOSE 3000

# Запуск сервера
CMD ["node", "index.js"] 