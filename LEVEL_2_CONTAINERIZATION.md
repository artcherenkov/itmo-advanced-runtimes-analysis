# Контейнеризации и Окружения

## 1. Общее устройство контейнеризации  

Проект `runtimes-benchmarks` полностью изолирует выполнение бенчмарков в Docker-контейнерах.  
Оркестрация разделена на два уровня:  

1. `docker-compose.yml` — долгоживущие сервисы для HTTP- и async-тестов.  
2. Bash-скрипты — одноразовые контейнеры для вычислительных (computational) и cold-start-бенчмарков, а также управление сервисами из п. 1 через `docker compose`.

Никаких других средств виртуализации (VM, Vagrant и т. д.) в кодовой базе не обнаружено; управляющие скрипты выполняются непосредственно на хост-ОС.

---

## 2. docker-compose.yml: определение сервисов

| Сервис | Образ/контекст | Порт host:container | Тип бенчмарка | Команда запуска |
|--------|----------------|---------------------|---------------|-----------------|
| `simple_http_node`  | `./benchmark-suites/node/http`  | `3001:3000` | HTTP            | `CMD ["node", "index.js"]` |
| `simple_http_deno`  | `./benchmark-suites/deno/http`  | `3002:3002` | HTTP            | `CMD ["deno", "run", "--allow-net", "--allow-env", "index.js"]` |
| `simple_http_bun`   | `./benchmark-suites/bun/http`   | `3003:3003` | HTTP            | `CMD ["bun", "index.js"]` |
| `simple_async_node` | `./benchmark-suites/node/async` | `3101:3000` | Async           | `command: node /app/src/index.js` *(volume-маунт кода)* |
| `simple_async_deno` | `./benchmark-suites/deno/async` | `3102:3000` | Async           | `command: deno run --allow-net --allow-env --allow-read --allow-write /app/src/index.js` |
| `simple_async_bun`  | `./benchmark-suites/bun/async`  | `3103:3000` | Async           | `command: bun run /app/src/index.js` |

Каждый сервис собирается из собственного `Dockerfile` (Node — `node:20`, Deno — `denoland/deno:latest`, Bun — `oven/bun:latest`) и прокидывает минимальный набор переменных окружения (`PORT`, `PARALLEL_TASKS`, …).

---

## 3. Использование Docker из скриптов

### 3.1 HTTP- и Async-бенчмарки (`scripts/run_http_benchmarks.sh`, `scripts/run_async_benchmarks.sh`)

Основные операции выполняются через **docker compose**-плагин:

```bash
# запуск выбранного сервиса в фоне
docker compose up -d $SERVICE

# остановка и удаление контейнера после теста
docker compose stop $SERVICE
```

Скрипт дополнительно:
* ждёт готовности контейнера (`curl` с /​ping или /​async-bench),
* генерирует нагрузку утилитой **wrk**,
* пишет результаты в `./results/(http|async)`.

### 3.2 Вычислительные бенчмарки  
Файл `scripts/run_computational_benchmarks.sh` вызывает рантайм-специфичные скрипты  
`benchmark-suites/*/computational/run_computational_benchmarks.sh`, где используется классическая схема *build-run-copy-destroy*:

```bash
# сборка образа
docker build -t $IMAGE_NAME -f ./benchmark-suites/<rt>/computational/Dockerfile .

# запуск одноразового контейнера с нужным тестом
docker run --name $container_name \
  --env BENCHMARK_TYPE=$test_type \
  --env ITERATIONS=$ITERATIONS \
  $IMAGE_NAME

# экспорт JSON-результатов
docker cp $container_name:/app/results/. ./results/

# удаление контейнера
docker rm $container_name
```

### 3.3 Cold-start-бенчмарки  
Каждый рантайм имеет собственный скрипт `benchmark-suites/<rt>/cold-start/cold_start_benchmark.sh`.

Ключевые Docker-операции:

| Цель | Команда |
|------|---------|
| Сборка образа | `docker build -t node-cold-start-benchmark -f benchmark-suites/node/cold-start/Dockerfile .` |
| Получить версию рантайма | `docker run --rm $IMAGE_NAME node -v` *(аналогично для Deno/Bun)* |
| Запуск контейнера в detach-режиме + публикация порта | `docker run --name <id> -d -p 3001:3000 $IMAGE_NAME` |
| Снятие логов для метки «READY_TIMESTAMP» | `docker logs <id>` |
| Замер системной информации | `docker exec <id> cat /etc/os-release` |
| Очистка | `docker stop <id>` + `docker rm <id>` |
| Гигиена | массовое удаление `docker ps -a | grep <name> | xargs docker rm -f` |

---

## 4. Требования к окружению хост-машины

### 4.1 Обязательные пакеты и утилиты

| Инструмент | Где упоминается | Назначение |
|------------|-----------------|-----------|
| **bash** | все `*.sh` | интерпретатор скриптов |
| **Docker Engine + docker CLI** | проверка `command -v docker` в cold-start скриптах | запуск контейнеров, сборка образов |
| **docker compose** *(плагин CLI)* | `docker compose up/stop` в HTTP/Async-скриптах | оркестрация сервисов из `docker-compose.yml` |
| **curl** | HTTP/Async + cold-start | проверки доступности сервисов, измерения |
| **wrk** | `scripts/run_http_benchmarks.sh` / `run_async_benchmarks.sh` | генерация HTTP-нагрузки |
| **jq** | cold-start | формирование/обновление JSON-файла результатов |
| **bc** | cold-start | вычисления с плавающей точкой при тайм-ауте |
| **python3** | cold-start | точный вывод меток времени в мс |
| **awk, sed, grep** | parsing в HTTP/Async-скриптах | извлечение метрик из вывода `wrk` |

Скрипты cold-start явно останавливаются с ошибкой, если `docker`, `curl`, `jq`, `bc` или `python3` не найдены:

```bash
if ! command -v jq > /dev/null; then
    log "Ошибка: jq не установлен"
    exit 1
fi
```

### 4.2 Рантаймы JavaScript на хосте

Ни один файл в директории `scripts/` не обращается к `node`, `deno` или `bun` напрямую; все вызовы происходят **только внутри контейнеров**.  
Следовательно, установка этих рантаймов на хост-машине не требуется.

---

## 5. Итоговая картина виртуализации

* **Изоляция кода и зависимостей** — Docker-контейнеры.  
* **Оркестрация** — плагин `docker compose`, одной `compose`-файл.  
* **Управление** — Bash-скрипты на хосте; никакой дополнительной виртуализации (VM, Vagrant) проект не использует.

Хост-ОС должна лишь удовлетворять перечню инструментов из раздела 4; вся логика бенчмарков, нужные версии Node.js/Deno/Bun и зависимые библиотеки инкапсулированы в образах, собираемых из репозитория.