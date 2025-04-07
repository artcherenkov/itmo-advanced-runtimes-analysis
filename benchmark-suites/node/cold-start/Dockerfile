FROM node:lts-alpine

WORKDIR /app

# Копирование серверного файла
COPY ./benchmark-suites/node/cold-start/server.js .

# Открываем порт для HTTP-сервера
EXPOSE 3000

# Запускаем сервер
CMD ["node", "server.js"] 