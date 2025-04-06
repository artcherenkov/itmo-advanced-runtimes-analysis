# HTTP-серверы на Node.js, Deno и Bun

Этот проект содержит простые HTTP-серверы, реализованные на трех JavaScript рантаймах: Node.js, Deno и Bun. Каждый сервер предоставляет идентичный API с эндпоинтом `/ping`, который отвечает строкой `pong`.

## Требования

- Docker
- Docker Compose

## Структура проекта

```
benchmark-suites/
├── node/
│   └── http/
│       └── index.js       # HTTP-сервер на Node.js
├── deno/
│   └── http/
│       └── index.js       # HTTP-сервер на Deno
└── bun/
    └── http/
        └── index.js       # HTTP-сервер на Bun

docker/
├── http-node/
│   └── Dockerfile         # Dockerfile для Node.js сервера
├── http-deno/
│   └── Dockerfile         # Dockerfile для Deno сервера
└── http-bun/
    └── Dockerfile         # Dockerfile для Bun сервера
```

## Запуск серверов

### Сборка образов

Для сборки Docker-образов для всех HTTP-серверов выполните:

```bash
docker compose build simple_http_node simple_http_deno simple_http_bun
```

Для сборки отдельного сервера:

```bash
docker compose build simple_http_node   # Только Node.js
docker compose build simple_http_deno   # Только Deno
docker compose build simple_http_bun    # Только Bun
```

### Запуск серверов

Для запуска всех серверов одновременно:

```bash
docker compose up simple_http_node simple_http_deno simple_http_bun -d
```

Для запуска отдельного сервера:

```bash
docker compose up simple_http_node -d   # Только Node.js
docker compose up simple_http_deno -d   # Только Deno
docker compose up simple_http_bun -d    # Только Bun
```

## Доступ к серверам

После запуска, серверы доступны по следующим адресам:

- Node.js: http://localhost:3001
- Deno: http://localhost:3002
- Bun: http://localhost:3003

## Тестирование

Для проверки работы серверов можно использовать `curl`:

```bash
curl http://localhost:3001/ping   # Проверка Node.js сервера
curl http://localhost:3002/ping   # Проверка Deno сервера
curl http://localhost:3003/ping   # Проверка Bun сервера
```

Каждый запрос должен вернуть ответ: `pong`

## Управление серверами

### Просмотр логов

```bash
docker compose logs simple_http_node   # Логи Node.js сервера
docker compose logs simple_http_deno   # Логи Deno сервера
docker compose logs simple_http_bun    # Логи Bun сервера
```

### Остановка серверов

```bash
docker compose stop simple_http_node simple_http_deno simple_http_bun  # Остановка всех
docker compose stop simple_http_node   # Остановка только Node.js
docker compose stop simple_http_deno   # Остановка только Deno
docker compose stop simple_http_bun    # Остановка только Bun
```

### Удаление контейнеров

```bash
docker compose down   # Удаление всех контейнеров
```

## Особенности реализации

Все три сервера имеют идентичный API, но используют специфичные для каждого рантайма API и возможности:

- Node.js использует встроенный модуль `http`
- Deno использует `Deno.serve` API
- Bun использует встроенный `Bun.serve` API

Это позволяет сравнить производительность и особенности каждого рантайма при выполнении идентичных задач. 