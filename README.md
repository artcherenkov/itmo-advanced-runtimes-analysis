# JavaScript Runtimes Benchmarking Suite

Набор бенчмарков для сравнения производительности различных JavaScript рантаймов (Node.js, Deno, Bun).

## Структура проекта

```
/runtimes-benchmarks
  /benchmark-suites      - Набор бенчмарков для разных рантаймов
    /metrics-interface.js - Общий интерфейс метрик
    /node                - Бенчмарки для Node.js
    /deno                - Бенчмарки для Deno
    /bun                 - Бенчмарки для Bun
  /results               - Результаты бенчмарков (JSON)
  /docker                - Докер-контейнеры для запуска бенчмарков
  benchmark-config.json  - Конфигурация экспериментов
  run-benchmarks.sh      - Скрипт для запуска экспериментов
```

## Поддерживаемые бенчмарки

1. **Фибоначчи** - Вычисление чисел Фибоначчи (рекурсивная и итеративная реализации)
   - Метрики: время выполнения, использование памяти, CPU

## Запуск бенчмарков

### Запуск через конфигурационный файл (рекомендуется)

Самый простой способ - использовать конфигурационный файл `benchmark-config.json` и скрипт `run-benchmarks.sh`:

```bash
# Убедитесь, что скрипт исполняемый
chmod +x run-benchmarks.sh

# Запустите все бенчмарки из конфигурации
./run-benchmarks.sh
```

Настройка экспериментов производится в файле `benchmark-config.json`:

```json
{
  "experiments": [
    {
      "name": "fibonacci",
      "description": "Вычисление чисел Фибоначчи",
      "runtimes": ["node"],
      "configurations": [
        {
          "parameters": {
            "n": 30,
            "implementation": "recursive",
            "iterations": 20
          }
        },
        {
          "parameters": {
            "n": 30,
            "implementation": "iterative",
            "iterations": 20
          }
        }
      ]
    }
  ]
}
```

### Запуск отдельных бенчмарков через Docker

#### Node.js Фибоначчи

```bash
# Сборка Docker-образа для Node.js
docker build -t js-benchmark-node -f docker/node/Dockerfile .

# Запуск бенчмарка с параметрами по умолчанию
docker run --rm -v "$(pwd)/results:/app/results" js-benchmark-node

# Запуск с пользовательскими параметрами
# FIB_N: номер числа Фибоначчи (по умолчанию 40)
# FIB_IMPL: тип реализации (recursive/iterative, по умолчанию recursive)
# ITERATIONS: количество итераций (по умолчанию 30)
docker run --rm -v "$(pwd)/results:/app/results" \
  --build-arg FIB_N=35 \
  --build-arg FIB_IMPL=iterative \
  --build-arg ITERATIONS=50 \
  js-benchmark-node
```

### Локальный запуск (без Docker)

#### Node.js Фибоначчи

```bash
# Включение принудительной сборки мусора
node --expose-gc benchmark-suites/node/fibonacci/index.js [n] [implementation] [iterations]

# Пример: Запуск с параметрами
node --expose-gc benchmark-suites/node/fibonacci/index.js 35 iterative 50
```

## Формат выходных данных

Результаты бенчмарков сохраняются в формате JSON со следующей структурой:

```json
{
  "runtime": "node|deno|bun",
  "version": "x.y.z",
  "experiment": "fibonacci_recursive_n40",
  "timestamp": "ISO-8601 timestamp",
  "environment": {
    "os": "linux",
    "container": true,
    "cpuCores": 4,
    "memory": "2GB"
  },
  "metrics": {
    "executionTimes": [...],
    "averageExecutionTime": 123456789,
    "memoryUsage": {
      "before": {...},
      "after": {...},
      "diff": {...}
    },
    "cpuUsage": {
      "before": {...},
      "after": {...},
      "diffUser": 123,
      "diffSystem": 456
    }
  },
  "statistics": {
    "mean": 123.45,
    "median": 120.3,
    "stdDev": 5.67,
    "p95": 130.1,
    "p99": 142.6
  },
  "detailedIterationMetrics": [
    {
      "iteration": 1,
      "executionTime": 123456,
      "memory": {
        "before": {...},
        "after": {...},
        "diff": {...}
      }
    },
    ...
  ]
}
```

## Особенности реализации

- **Деоптимизация кода**: Все бенчмарки используют специальные техники для обхода оптимизаций движка JavaScript, чтобы обеспечить более честное сравнение.
- **Метрики**: Сбор подробных метрик о времени выполнения, использовании памяти и CPU.
- **Детальные метрики итераций**: Запись времени выполнения и использования памяти для каждой итерации.
- **Стабилизация**: Принудительная сборка мусора и паузы для стабилизации системы перед каждым измерением.
- **Статистика**: Расчет среднего, медианы, стандартного отклонения и процентилей для всех измерений.

## Требования

- Docker
- Node.js (для локального запуска)
- jq (для работы с JSON в скриптах) 