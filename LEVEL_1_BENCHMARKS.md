# Состав бенчмарков

## 1. Структура каталога `benchmark-suites/`

```
benchmark-suites/
├── metrics-interface.mjs             # общий интерфейс сбора метрик
├── node/                             # тесты для Node.js
│   ├── computational/
│   ├── http/
│   ├── async/
│   └── cold-start/
├── deno/                             # тесты для Deno
│   └── … (та же иерархия)
└── bun/                              # тесты для Bun
    └── … (та же иерархия)
```

Четыре логические категории бенчмарков представлены одноимёнными подпапками внутри каждого рантайма:

* `computational` – интенсивные вычисления без I/O;
* `http` – минимальные HTTP-серверы для оценки отклика;
* `async` – композиция параллельных асинхронных задач (сетевых, файловых, таймеров);
* `cold-start` – измерение времени «холодного» старта контейнера и первого ответа приложения.

---

## 2. Реализованные тесты по категориям

### 2.1 Computational

| Задача | Файл | Ключевые варианты реализации |
|--------|------|-----------------------------|
| Числа Фибоначчи | `fibonacci.js` | `recursive`, `iterative` (через `FIB_IMPL`) |
| Сортировка массива | `sorting.js` | `quicksort`, `insertion` (`SORT_ALGORITHM`) |
| Умножение матриц | `matrix.js` | `naive`, `optimized` (`MATRIX_ALGORITHM`) |
| JSON-операции | `json.js` | `parse-stringify`, `deep-clone` (`JSON_OPERATION`) |

Файлы идентичны по именам во всех трёх рантаймах. Алгоритмическая логика общая; отличия касаются:

* способа импорта стандартных модулей (`import path from 'path'` в Node/Bun ↔️ `import * as path from 'https://deno.land/std/path/mod.ts'` в Deno);
* получения переменных среды (`process.env` ↔️ `Deno.env.get()` ↔️ `process.env` в Bun);
* возможности принудительного GC (доступно в Node/Bun, отсутствует в Deno – выводится информационное сообщение);
* пути сохранения результатов задаётся одинаково, но формируется через API соответствующей платформы.

### 2.2 HTTP

Каждый рантайм содержит единственный файл `index.js`, реализующий энд-пойнт `GET /ping`:

* Node.js — `http.createServer` (`benchmark-suites/node/http/index.js`).
* Deno — `Deno.serve` (`benchmark-suites/deno/http/index.js`).
* Bun — `Bun.serve` (`benchmark-suites/bun/http/index.js`).

Логика обработки одинаковая: «pong» при `/ping`, `404` иначе.

### 2.3 Async

Файл `async/index.js` моделирует смесь асинхронных задач:

1. файловые операции (создание, запись, чтение, удаление временного файла);
2. искусственные сетевые задержки (`mockExternalApiCall()`);
3. случайные `setTimeout`-задержки.

Реализация одинакова по структуре, но использует разные API:

* Node — `fs/promises`, `crypto.randomBytes`;
* Deno — `Deno.writeFile`, `crypto.getRandomValues` с лимитом 64 КБ;
* Bun — `Bun.write`, `Bun.file`, собственный импорт `import { file } from 'bun'`.

### 2.4 Cold-start

Каталог содержит:

* `server.js` — минимальный HTTP-сервер, выводящий метку времени `READY_TIMESTAMP` сразу после старта;
* `cold_start_benchmark.sh` — bash-скрипт (≈ 440 стр.) собирающий Docker-образ, многократно запускающий контейнер и вычисляющий метрики:
  * время запуска рантайма (T1 − T0);
  * задержку до первого ответа (T2 − T1);
  * общее время холодного старта (T2 − T0).

Структура скриптов одинакова, но команды внутри контейнера разные (`node`, `deno`, `bun`).

---

## 3. Унификация кода между рантаймами

| Категория | Степень совпадения | Существенные отличия |
|-----------|-------------------|-----------------------|
| Computational | 90 % общих строк | системные импорты, доступ к env-переменным, вызов GC |
| HTTP | ~70 % | API создания сервера (`http`, `Deno.serve`, `Bun.serve`) |
| Async | ~75 % | API файловой системы и криптографии, способ удаления файла |
| Cold-start | скрипт Shell почти идентичен | имя базового образа и команда запуска рантайма |

Таким образом, код старается быть максимально переносимым, но сохраняет идиоматичность конкретного рантайма.

---

## 4. Использование `metrics-interface.mjs`

Только вычислительные тесты используют единый слой сбора метрик:

1. Каждая реализация подключает обёртку

```javascript
// пример: benchmark-suites/node/computational/utils/metrics.mjs
import { formatMetrics, saveResults } from '../../../metrics-interface.mjs';
```

2. Функция `benchmark()` (определена в `utils/metrics.mjs`) измеряет время, память и CPU, затем вызывает

```javascript
const metrics = formatMetrics(
  'node',                 // идентификатор рантайма
  process.version,        // версия
  experiment,             // название эксперимента
  executionTimes,         // массив временемеров
  { before: memoryBefore, after: memoryAfter },
  { before: cpuBefore, after: cpuAfter, cpuCores: cpuBefore.cpuCores }
);

await saveResults(metrics, outputPath);
```

3. Внутри `saveResults()` реализованы ветки для трёх платформ;
   функция сама создаёт директорию и пишет JSON-файл:

```javascript
// Фрагмент из metrics-interface.mjs (ветка Node/Bun)
const { writeFileSync, mkdirSync, existsSync } = await import('fs');
...
writeFileSync(outputPath, JSON.stringify(results, null, 2));
```

Таким образом обеспечивается унифицированный формат отчётов *при полной независимости от специфики рантайма*.

---

## 5. Роль `Dockerfile` в каталагах бенчмарков

Dockerfile присутствует в каждой подкатегории для:

1. **Изоляции среды** — выбор базового образа (`node:20`, `denoland/deno:latest`, `oven/bun`) обеспечивает стабильную версию рантайма.
2. **Копирования только нужных файлов** бенчмарка и общего `metrics-interface.mjs`.
3. **Задания переменных окружения** (например, `ITERATIONS`, параметры теста, `CONTAINER=true`).
4. **Включения необходимых флагов** — напр. `NODE_OPTIONS="--expose-gc"` для Node.
5. **Точки входа** — команда `CMD` запускает конкретный скрипт или сервер, иногда с учётом переменной `BENCHMARK_TYPE`.

Пример (укорочено, `node/computational/Dockerfile`):

```dockerfile
ENV BENCHMARK_TYPE=fibonacci
CMD ["sh", "-c", "if [ \"$BENCHMARK_TYPE\" = \"fibonacci\" ]; then node fibonacci.js; ... fi"]
```

Таким образом Docker-образы обеспечивают повторяемость результатов и используются вспомогательными shell-скриптами (`run_computational_benchmarks.sh`, `cold_start_benchmark.sh`) для массового запуска испытаний.

---

## 6. Итог

Каталог `benchmark-suites/` предоставляет однообразный набор испытаний для трёх JavaScript-рантаймов. Общий интерфейс метрик и идентичные алгоритмы гарантируют корректность сравнения, а Docker-контейнеры делают процесс запуска детерминированным и переносимым. 