# Интерпретация результатов HTTP-бенчмаркинга

В этой директории представлены результаты сравнительного анализа производительности HTTP-серверов на различных JavaScript рантаймах: Node.js, Deno и Bun.

## Содержание

1. [Общая информация](#общая-информация)
2. [Пропускная способность (RPS)](#пропускная-способность-rps)
3. [Анализ задержек](#анализ-задержек)
4. [Стабильность производительности](#стабильность-производительности)
5. [Радарная диаграмма](#радарная-диаграмма)

## Общая информация

Бенчмаркинг проводился с использованием следующих параметров:
- 4 потока
- 100 одновременных соединений
- Продолжительность теста: 30 секунд
- 3 итерации для каждого рантайма
- Тестовый эндпоинт: `/ping`

## Пропускная способность (RPS)

Файл: `1_http_rps_comparison.png`

Эта диаграмма показывает среднюю пропускную способность каждого рантайма, измеренную в запросах в секунду (RPS).

**Как интерпретировать:**
- Высота столбцов отражает среднее количество запросов в секунду
- Планки погрешности показывают стандартное отклонение между итерациями
- Числа над столбцами — точные значения средних RPS

Более высокие значения RPS указывают на лучшую пропускную способность сервера.

## Анализ задержек

Файл: `2_http_latency_comparison.png`

Эта диаграмма отображает две ключевые метрики задержек для каждого рантайма:
- Средняя задержка (более темные столбцы)
- Максимальная задержка (более светлые столбцы с штриховкой)

**Как интерпретировать:**
- Ось Y использует логарифмическую шкалу для лучшего отображения больших различий
- Меньшие значения лучше (означают более быстрые ответы)
- Разница между средней и максимальной задержкой показывает "хвосты распределения"

*Примечание:* Логарифмическая шкала позволяет визуализировать как малые, так и большие значения на одном графике.

## Стабильность производительности

Файл: `3_http_stability_comparison.png`

Линейная диаграмма показывает, как производительность (RPS) меняется между итерациями для каждого рантайма.

**Как интерпретировать:**
- Каждая точка представляет одну итерацию теста
- Пунктирные горизонтальные линии показывают среднее значение RPS для каждого рантайма
- Более плоские линии указывают на более стабильную производительность
- Резкие скачки могут указывать на проблемы со стабильностью или влияние сборки мусора

Стабильная производительность особенно важна для приложений, обрабатывающих постоянный поток запросов.

## Радарная диаграмма

Файл: `4_http_radar_comparison.png`

Радарная диаграмма объединяет пять ключевых метрик в едином представлении для комплексной оценки производительности. Все метрики нормализованы, где 1.0 (внешний край) представляет лучшее значение.

**Метрики:**

1. **Средний RPS**
   - Нормализован к максимальному значению RPS среди всех рантаймов
   - Ближе к 1.0 = выше пропускная способность

2. **Минимальная средняя задержка**
   - Инвертирована и нормализована (минимальная задержка / задержка рантайма)
   - Ближе к 1.0 = меньше задержка ответа

3. **Стабильность RPS**
   - Рассчитана как 1 - коэффициент вариации
   - Ближе к 1.0 = более стабильная пропускная способность

4. **Стабильность задержек**
   - Инвертирована и нормализована (минимальный CV / CV рантайма)
   - Ближе к 1.0 = более предсказуемое время ответа

5. **Устойчивость к пиковым нагрузкам**
   - Инвертирована и нормализована (минимальная максимальная задержка / максимальная задержка рантайма)
   - Ближе к 1.0 = лучшая устойчивость к пиковым нагрузкам

**Как интерпретировать:**
- Большая площадь многоугольника указывает на лучшую общую производительность
- Равномерное распределение по всем осям указывает на сбалансированную производительность
- Провалы в определённых метриках указывают на потенциальные области для оптимизации

Радарная диаграмма особенно полезна для быстрого сравнения сильных и слабых сторон разных рантаймов.

## Формулы расчета метрик

**Коэффициент вариации (CV):**
```
CV = (стандартное_отклонение / среднее_значение) * 100%
```

**Нормализация метрик к диапазону [0,1]:**
- Для метрик где "больше лучше": `значение / макс_значение`
- Для метрик где "меньше лучше": `мин_значение / значение`

**Устойчивость к пиковым нагрузкам:**
Рассчитывается как среднее значение максимальных задержек по всем итерациям теста:
```
mean_latency_max = avg(max_latency_iteration_1, max_latency_iteration_2, max_latency_iteration_3)
```

Затем нормализуется к лучшему значению:
```
peak_resilience = min_mean_latency_max / runtime_mean_latency_max
``` 