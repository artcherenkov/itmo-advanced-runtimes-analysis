## 1. Общий конвейер сбора и сохранения метрик

Ниже описан полный путь прохождения данных о производительности — от момента съёма в тестах до записи в файл `results/`. Все утверждения подтверждены реализацией в исходном коде проекта `runtimes-benchmarks`.

---

### 1.1. Вычислительные бенчмарки (`benchmark-suites/*/computational`)

1. **Платформенно-специфические тесты** (например, `sorting.js`, `matrix.js`) импортируют утилиту `benchmark()` из
  ```
  benchmark-suites/node/computational/utils/metrics.mjs
  ```
   и вызывают её с параметрами количества итераций, названия эксперимента и целевого пути для результатов.
2. `benchmark()` перед началом теста собирает исходные характеристики окружения:
   * `getCpuUsage()` — сводный `user/sys/idle` тайм **для всех ядер**;
   * `getMemoryUsage()` — снэпшот `process.memoryUsage()` + общая/свободная RAM.
3. Для каждой итерации цикла выполняется:
   1. «Разогрев» GC и короткая стабилизация `stabilizeSystem()`.
   2. Точное измерение **времени выполнения** с помощью `process.hrtime.bigint()` (наносекунды).
   3. Замер памяти _до_ и _после_ вызова тестируемой функции с расчётом `diff`.
   4. Сохранение сырых значений в массивы `executionTimes[]` и `detailedIterationMetrics[]`.
4. По завершении всех итераций массив `executionTimes` передаётся в
   ```
   benchmark-suites/metrics-interface.mjs
   ```
   Функция `formatMetrics()` агрегирует статистику:
   * среднее `mean`, медиану `median`;
   * стандартное отклонение `stdDev`;
   * перцентили `p95`, `p99`.
   Она также формирует единый объект результата, включающий разделы `environment`, `metrics`, `statistics` и (опционально) `detailedIterationMetrics`.
5. Готовый объект сохраняется функцией `saveResults()` (тот же файл) в `JSON`, причём путь формируется из параметра `outputPath`; примеры имён:
   ```text
   results/computational/node_fibonacci_recursive_n40_<timestamp>.json
   results/computational/deno_sorting_quicksort_size10000_<timestamp>.json
   ```

### 1.2. HTTP-серверы (`scripts/run_http_benchmarks.sh`)

1. Скрипт принимает `<runtime>` и число `iterations`, поднимает нужный сервис командой `docker compose up -d <service>`.
2. После проверки здоровья сервер обстреливается утилитой `wrk`:
   ```bash
   wrk -t4 -c100 -d30s http://localhost:<port>/ping > /tmp/wrk_output.txt
   ```
3. Сырые метрики извлекаются `grep`/`awk`-парсерами:
   * блок `Latency` → `avg / stdev / max`;
   * блок `Req/Sec` с обработкой суффикса `k` (×1000);
   * строка `requests in …` → `total_requests` и `duration_seconds`;
   * строка `Requests/sec:` и `Transfer/sec:`.
4. Каждый запуск `wrk` формирует JSON-элемент в массиве `iterations` со структурой `results.{latency, requests_per_sec, summary}` + строкой `raw_output`.
5. Итоговый файл сохраняется как
   ```text
   results/http/<runtime>_http_<timestamp>.json
   ```
   Полей агрегации по всем итерациям скрипт **не** вычисляет — они добавляются позже утилитами из `analysis/`.

### 1.3. Асинхронные задачи (`scripts/run_async_benchmarks.sh`)

Процесс идентичен HTTP, но дополнительно после каждого прогона выполняется `curl` на эндпоинт `/async-bench`, ответ которого содержит пользовательскую метрику `duration_ms`. Значение помещается в `summary.server_async_duration_ms`, а весь JSON ответа — в поле `server_response`.

### 1.4. Холодный старт (`benchmark-suites/*/cold-start/cold_start_benchmark.sh`)

1. Скрипт билдит образ `<runtime>-cold-start-benchmark` и задаёт уникальное имя контейнера.
2. Внутри каждой итерации фиксируются три отметки времени:
   * `T0` — старт контейнера (`python3 -c 'time.time()*1000'`).
   * `T1` — момент готовности сервера, считывается из логов `docker logs … | grep READY_TIMESTAMP:`.
   * `T2` — время первого успешного запроса `curl` к корневому эндпоинту.
3. Метрики вычисляются как разности:
   * `startup_time_ms = T1 - T0`;
   * `first_request_time_ms = T2 - T1`;
   * `total_cold_start_time_ms = T2 - T0`.
4. Дополнительные данные собираются:
   * системная информация хоста (`uname`, `/proc/cpuinfo`, `free -m`, `sysctl`) — функция `get_system_info()`;
   * параметры контейнера (`cpu.shares`, memory-limits) — `get_node_environment()` (по аналогу в Deno/Bun).
5. Результаты каждой итерации добавляются в JSON через `jq`, а файл создаётся под именем
   ```text
   results/cold-start/<runtime>_cold_start_benchmark_<timestamp>.json
   ```

---

## 2. Обработка и агрегирование

| Тип теста | Где происходит обработка | Что агрегируется |
|-----------|--------------------------|------------------|
| Вычислительные | `formatMetrics()` | `executionTimes[] → mean/median/stdDev/p95/p99`, а также диффы по памяти/CPU |
| HTTP / Async | `run_http_benchmarks.sh`, `run_async_benchmarks.sh` | **не агрегируется**; сохраняются метрики каждой итерации. |
| Cold-Start | `cold_start_benchmark.sh` | Скрипт рассчитывает разницы времени, но сводных статистик (mean/p95) не формирует. |

---

## 3. Иерархия `results/`

```text
results/
├── computational/
│   └── <runtime>_<experiment>_<timestamp>.json
├── http/
│   └── <runtime>_http_<timestamp>.json
├── async/
│   └── <runtime>_async_<timestamp>.json
└── cold-start/
    └── <runtime>_cold_start_benchmark_<timestamp>.json
```
*`<runtime>` ∈ {`node`, `deno`, `bun`}; `<timestamp>` генерируется через `date +%Y%m%d%H%M%S` или `Date.now()`.*

---

## 4. Формат файлов результатов

### 4.1. Вычислительные (сокращённый пример)
```json
{
  "runtime": "node",
  "version": "v20.19.0",
  "experiment": "fibonacci_recursive_n40",
  "timestamp": "2025-04-09T02:30:09.271Z",
  "environment": { "os": "linux", "container": true, "cpuCores": 8, "memory": "7838MB" },
  "metrics": {
    "executionTimes": [951233833, 946152042],
    "averageExecutionTime": 948692937.5,
    "memoryUsage": { "before": {…}, "after": {…}, "diff": {…} },
    "cpuUsage": { "before": {…}, "after": {…}, "diffUser": 1960, "diffSystem": 0 }
  },
  "statistics": { "mean": 948692937.5, "median": 951233833, "stdDev": 2540895.5, "p95": 951233833, "p99": 951233833 },
  "detailedIterationMetrics": [ { "iteration": 1, … }, { "iteration": 2, … } ]
}
```

### 4.2. HTTP / Async (фрагмент)
```json
{
  "runtime": "bun",
  "timestamp": "2025-04-09T09:33:54",
  "configuration": { "threads": 4, "connections": 100, "duration": "30s", "url": "…", "iterations": 2 },
  "iterations": [
    {
      "iteration": 1,
      "timestamp": "…",
      "success": true,
      "results": {
        "latency": { "avg": "4.73ms", "stdev": "5.67ms", "max": "160.02ms" },
        "requests_per_sec": { "avg": 5890, "stdev": 1270, "max": 8320 },
        "summary": { "total_requests": 702874, "duration_seconds": 30.01, "requests_per_sec": 23420.14, "transfer_per_sec": "3.39MB" }
      },
      "raw_output": "Running 30s test …"
    }
  ],
  "success": true
}
```

### 4.3. Cold-Start (фрагмент)
```json
{
  "runtime": "deno",
  "version": "1.43.0",
  "host_system": { "os_type": "Darwin", "cpu_cores": 8, … },
  "iterations": [
    { "iteration": 1, "startup_time_ms": 242, "first_request_time_ms": 162, "total_cold_start_time_ms": 404 },
    { "iteration": 2, "startup_time_ms": 165, "first_request_time_ms": 62,  "total_cold_start_time_ms": 227 }
  ]
}
```

---

## 5. Директория `analysis/`

Каталог `analysis/` содержит **пост-обработку** и визуализацию.
Например, `analysis/computational/benchmark_visualization.py` строит графики распределения времени выполнения, используя файлы из `results/computational/`. Эти инструменты **не участвуют** в создании первичных файлов; они читают готовые JSON, агрегируют статистику (при необходимости) и формируют отчёты/графики для презентации. 