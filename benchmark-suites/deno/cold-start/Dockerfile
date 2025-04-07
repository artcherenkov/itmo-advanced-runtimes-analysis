FROM denoland/deno:latest

WORKDIR /app

# Копирование серверного файла
COPY ./benchmark-suites/deno/cold-start/server.js .

# Открываем порт для HTTP-сервера
EXPOSE 3000

# Запускаем сервер с необходимыми правами
CMD ["deno", "run", "--allow-net", "--allow-env", "server.js"] 