# Технический анализ проекта `runtimes-benchmarks`

## 1. Структура директорий

```
/ (корень проекта)
├── scripts/             # Bash-скрипты-оркестраторы
├── benchmark-suites/    # Исходный код всех бенчмарков
├── results/             # Сгенерированные JSON-отчёты
├── analysis/            # Утилиты пост-обработки результатов
├── docker-compose.yml   # Описание сервисов для HTTP/async
└── README-*.md
```

- **scripts/** — обёртки для запуска групп тестов (`run_all_benchmarks.sh`, `run_computational_benchmarks.sh`, `run_http_benchmarks.sh`, `run_async_benchmarks.sh`).
- **benchmark-suites/** — папки по рантаймам (`node`, `deno`, `bun`), внутри — по типам нагрузок (`computational`, `http`, `async`, `cold-start`).
- **results/** — сохраняет отчёты:
  - `results/computational/`
  - `results/http/`
  - `results/async/`
  - `results/cold-start/`
- **analysis/** — Python-скрипты и Jupyter/утилиты для визуализации и агрегации.

## 2. Скрипт-оркестратор `run_all_benchmarks.sh`

Расположен в `scripts/run_all_benchmarks.sh`. Основные задачи:
1. Парсинг CLI-опций и валидация (см. help):

```30:38:scripts/run_all_benchmarks.sh
  echo "  -a, --all               Запустить все тесты для всех рантаймов"
  echo "  -c, --computational     Запустить вычислительные тесты"
  echo "  -h, --http              Запустить HTTP бенчмарки"
  echo "  -s, --async             Запустить асинхронные бенчмарки"
  echo "  -d, --cold-start        Запустить тесты холодного старта"
  echo "  -r, --runtime RUNTIME   Рантайм ..."
  echo "  -i, --iterations NUM    Количество итераций"
  echo "  -v, --verbose           Подробный вывод"
```

2. Формирует массивы `RUNTIMES` и булевы флаги для типов тестов.
3. Делегирует запуск:
   - `run_computational_benchmarks.sh`
   - `run_http_benchmarks.sh`
   - `run_async_benchmarks.sh`
   - `benchmark-suites/$runtime/cold-start/cold_start_benchmark.sh`

Пример вызова HTTP-скрипта внутри цикла:

```85:92:scripts/run_all_benchmarks.sh
for runtime in "${RUNTIMES[@]}"; do
  log "=== HTTP для $runtime ==="
  bash ./scripts/run_http_benchmarks.sh $runtime $ITERATIONS
```

Финальная сводка выводит общее время и путь к `./results`.

## 3. Специализированные скрипты в `scripts/`

- **run_computational_benchmarks.sh** — запускает для каждого рантайма соответствующий Docker-скрипт-обёртку в `benchmark-suites/<runtime>/computational`.
- **run_http_benchmarks.sh** — поднимает сервис из `docker-compose.yml`, ждёт `/ping`, прогоняет `wrk`, парсит вывод и пишет в JSON:

```20:26:scripts/run_http_benchmarks.sh
RESULTS_DIR="./results/http"
RESULTS_FILE="${RESULTS_DIR}/${RUNTIME}_http_${TIMESTAMP}.json"
```

- **run_async_benchmarks.sh** — аналогично, но точка `/async-bench`, плюс вытаскивает JSON-ответ сервера (`server_response`) и поле `server_async_duration_ms`.

## 4. Структура `benchmark-suites/`

```
benchmark-suites/
├── node/
│   ├── computational/   # Dockerfile + JS-тесты (fibonacci.js, sorting.js,...)
│   ├── http/            # Dockerfile + HTTP-server
│   ├── async/           # Dockerfile + async I/O benchmark
│   └── cold-start/      # cold_start_benchmark.sh
├── deno/  (аналогично)
└── bun/   (аналогично)
```

В каждом `computational/run_computational_benchmarks.sh` строится образ, запускаются контейнеры под каждый тест, результаты копируются в `./results/computational`.

## 5. Интерфейс метрик — `metrics-interface.mjs`

Содержит две функции:

```1:9:benchmark-suites/metrics-interface.mjs
export function formatMetrics(runtime, version, experiment, executionTimes, memoryUsage, cpuUsage) { ... }
```

- **formatMetrics** — генерирует единый JSON со статистикой (mean, median, p95, p99, stdDev) и данными окружения (OS, container).
- **saveResults** — кросс-рантайм-функция для сохранения JSON-файла (Node.js/Bun через `fs`, Deno через `Deno.writeTextFileSync`).

## 6. Обработка и хранение результатов

- Отчёты **computational** генерируются «в контейнере» и копируются на хост.
- HTTP/async → `wrk` → итерации → массив `iterations: [ … ]` в JSON.
- Cold-start → многократное измерение времени старта и первого запроса + системные метрики → единый JSON.

## 7. Зависимости и окружение

- Docker & **docker-compose**
- **wrk**, **curl**, **jq**, **bc**, **python3** (cold-start)
- Локальные рантаймы (node/deno/bun) внутри образов или в PATH
- Compose-сервисы описаны в `docker-compose.yml`:

```1:14:docker-compose.yml
services:
  simple_http_node:
    build: { context: ./benchmark-suites/node/http }
  simple_async_node: ...
```

## 8. Логирование и вывод

- Цветной ANSI-вывод установленных констант: `GREEN='[0;32m'`, `BLUE`, `YELLOW`, `RED`, `NC`.
- В оркестраторе `log()` печатает timestamp при `--verbose` или для важных сообщений.
- Контейнерные скрипты используют `echo -e "\033[1;32m...\033[0m"` для статуса.

---

*Файл сгенерирован автоматически на основании анализа кода проекта.* 