#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Настройка стилей для графиков
plt.style.use('ggplot')
sns.set(font_scale=1.1)
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (8, 5)  # Уменьшаем размеры графиков
plt.rcParams['figure.autolayout'] = True  # Автоматический лэйаут
plt.rcParams['figure.constrained_layout.use'] = True  # Улучшенный лэйаут для избежания наложений

# Функция для добавления описания к графикам
def add_description_to_figure(fig, title, description, interpretation):
    """
    Добавляет блок с описанием и интерпретацией к графику.
    
    Args:
        fig: Объект Figure
        title: Заголовок описания
        description: Текст описания графика
        interpretation: Текст с рекомендациями по интерпретации
    """
    # Создаем текст для добавления
    text = f"""
    {title}
    
    Описание:
    {description}
    
    Как интерпретировать:
    {interpretation}
    """
    
    # Добавляем текстовый блок внизу графика
    fig.text(0.5, 0.01, text, ha='center', va='bottom', fontsize=9, 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Делаем фигуру выше, чтобы вместить описание
    fig_height = fig.get_figheight()
    fig.set_figheight(fig_height + 2.5)  # Увеличиваем высоту на 2.5 дюйма
    
    return fig

# Функция для загрузки результатов тестирования
def load_benchmark_results(results_dir='results', experiment_type='fibonacci_recursive'):
    """Загружает результаты тестов производительности из директории."""
    results = {'node': None, 'deno': None, 'bun': None}
    
    for filename in os.listdir(results_dir):
        if experiment_type in filename:
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
                runtime = data.get('runtime')
                if runtime in results:
                    results[runtime] = data
    
    return results

# Функция для загрузки результатов тестирования для конкретного рантайма
def load_runtime_benchmark_results(runtime, results_dir='results', experiment_type='fibonacci_recursive'):
    """Загружает результаты тестов производительности из директории для заданного рантайма."""
    runtime_results = None
    
    for filename in os.listdir(results_dir):
        if experiment_type in filename and runtime in filename:
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
                if data.get('runtime') == runtime:
                    runtime_results = data
            if runtime_results:
                break  # Нашли результаты для заданного рантайма
    
    return runtime_results

# Функция для расчета эвристики потребления памяти
def calculate_memory_heuristic(memory_data):
    """
    Рассчитывает эвристику потребления памяти по формуле:
    (RSS + heapTotal + 2*heapUsed)/4
    """
    rss = memory_data.get('rss', 0)
    heap_total = memory_data.get('heapTotal', 0)
    heap_used = memory_data.get('heapUsed', 0)
    
    return (rss + heap_total + 2*heap_used) / 4

# Функция для построения столбчатой диаграммы средних времён выполнения
def plot_average_execution_times(results, save_path=None):
    """Строит столбчатую диаграмму средних времён выполнения."""
    runtimes = []
    avg_times = []
    std_devs = []
    
    for runtime, data in results.items():
        if data:
            runtimes.append(runtime)
            # Преобразуем из наносекунд в миллисекунды
            avg_time_ms = data['metrics']['averageExecutionTime'] / 1_000_000
            avg_times.append(avg_time_ms)
            std_dev_ms = data['statistics']['stdDev'] / 1_000_000
            std_devs.append(std_dev_ms)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(runtimes, avg_times, yerr=std_devs, capsize=10, 
            color=['#3498db', '#2ecc71', '#e74c3c'])
    
    ax.set_ylabel('Среднее время выполнения (мс)')
    ax.set_title('Сравнение среднего времени выполнения по рантаймам')
    
    # Добавление значений на столбцы
    for i, bar in enumerate(bars):
        height = bar.get_height()
        std_dev = std_devs[i]  # Получаем стандартное отклонение для текущего столбца
        
        # Добавляем подпись с средним значением и стандартным отклонением на разных строках
        # и устанавливаем фон для текста
        ax.annotate(f'{height:.2f} (σ={std_dev:.2f})', 
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.7))
    
    # Добавляем описание и интерпретацию
    title = "Средние времена выполнения"
    description = """
    Эта столбчатая диаграмма показывает среднее время выполнения тестируемого алгоритма для трех JavaScript рантаймов: 
    Node.js, Deno и Bun. Планки погрешностей (вертикальные линии) показывают стандартное отклонение, 
    которое указывает на вариативность времени выполнения.
    """
    interpretation = """
    1. Более низкий столбец означает более быстрое выполнение (лучшую производительность).
    2. Меньшее стандартное отклонение (σ) означает более стабильную производительность.
    3. При сравнении рантаймов обращайте внимание как на абсолютные значения (высоту столбцов), 
       так и на их стандартные отклонения.
    4. Рантайм с низким средним временем и низким стандартным отклонением является наиболее предсказуемо быстрым.
    """
    fig = add_description_to_figure(fig, title, description, interpretation)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout()
    return fig, ax

# Функция для построения boxplot распределения времени выполнения
def plot_execution_time_boxplot(results, save_path=None):
    """Строит boxplot распределения времени выполнения."""
    data = []
    runtime_names = []
    
    for runtime, result in results.items():
        if result:
            # Преобразуем из наносекунд в миллисекунды
            times_ms = [t / 1_000_000 for t in result['metrics']['executionTimes']]
            data.append(times_ms)
            runtime_names.append(runtime)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    box = ax.boxplot(data, patch_artist=True, labels=runtime_names)
    
    # Установка логарифмической шкалы для оси Y
    ax.set_yscale('log')
    
    # Установка цветов для boxplot
    colors = ['#3498db', '#2ecc71', '#e74c3c']
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
    
    ax.set_ylabel('Время выполнения (мс)')
    ax.set_title('Распределение времени выполнения по рантаймам')
    
    # Добавляем описание и интерпретацию
    title = "Распределение времени выполнения (Boxplot)"
    description = """
    Этот boxplot показывает распределение времени выполнения для каждого рантайма. 
    Используется логарифмическая шкала для лучшего отображения данных с большим разбросом.
    
    Элементы каждого boxplot:
    - Центральная линия: медиана (50-й процентиль)
    - Нижняя граница коробки: 1-й квартиль (25-й процентиль)
    - Верхняя граница коробки: 3-й квартиль (75-й процентиль)
    - Усы: распространяются до наиболее отдаленных точек в пределах 1.5*IQR
    - Точки: выбросы (значения, выходящие за пределы усов)
    """
    interpretation = """
    1. Более низкое расположение коробки означает более быстрое выполнение алгоритма.
    2. Меньший размер коробки означает более стабильную производительность.
    3. Выбросы (точки) указывают на аномальные измерения - особенно медленные или быстрые выполнения.
    4. Наличие множества выбросов может указывать на нестабильность рантайма.
    5. При логарифмической шкале важно обращать внимание на пропорциональную разницу между рантаймами.
    """
    fig = add_description_to_figure(fig, title, description, interpretation)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout()
    return fig, ax

# Функция для построения графика потребления памяти
def plot_memory_usage(results, save_path=None):
    """Строит столбчатую диаграмму эвристики потребления памяти."""
    runtimes = []
    memory_usages = []
    
    for runtime, data in results.items():
        if data:
            runtimes.append(runtime)
            memory_before = data['metrics']['memoryUsage']['before']
            memory_after = data['metrics']['memoryUsage']['after']
            
            # Рассчитываем нашу эвристику для состояния до и после
            memory_heuristic_before = calculate_memory_heuristic(memory_before)
            memory_heuristic_after = calculate_memory_heuristic(memory_after)
            
            # Используем среднее значение эвристики
            avg_memory_heuristic = (memory_heuristic_before + memory_heuristic_after) / 2
            
            # Преобразуем в МБ для удобства восприятия
            memory_usages.append(avg_memory_heuristic / (1024 * 1024))
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(runtimes, memory_usages, color=['#3498db', '#2ecc71', '#e74c3c'])
    
    ax.set_ylabel('Потребление памяти (МБ)')
    ax.set_title('Сравнение потребления памяти по рантаймам')
    
    # Добавление значений на столбцы
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    # Добавляем описание и интерпретацию
    title = "Потребление памяти"
    description = """
    Эта столбчатая диаграмма показывает среднее потребление памяти для каждого рантайма при выполнении тестового алгоритма.
    Используется эвристическая формула: (RSS + heapTotal + 2*heapUsed)/4, где: 
    - RSS: общая память процесса 
    - heapTotal: общий размер выделенной памяти в куче JavaScript
    - heapUsed: фактически используемая память в куче
    """
    interpretation = """
    1. Более низкий столбец означает более эффективное использование памяти.
    2. При оценке следует учитывать не только абсолютные значения, но и контекст использования:
       - Для ограниченных сред (например, мобильных устройств) низкое потребление памяти может быть критичным.
       - В средах с большим объемом памяти важнее может быть скорость, а не экономия памяти.
    3. Большое потребление памяти может указывать на неоптимальное управление памятью или особенности реализации рантайма.
    """
    fig = add_description_to_figure(fig, title, description, interpretation)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout()
    return fig, ax

# Функция для построения графика зависимости время-память
def plot_time_vs_memory(results, save_path=None):
    """Строит диаграмму рассеяния время выполнения против потребления памяти."""
    runtimes = []
    avg_times = []
    memory_usages = []
    
    for runtime, data in results.items():
        if data:
            runtimes.append(runtime)
            
            # Время в мс
            avg_time_ms = data['metrics']['averageExecutionTime'] / 1_000_000
            avg_times.append(avg_time_ms)
            
            # Память в МБ
            memory_before = data['metrics']['memoryUsage']['before']
            memory_after = data['metrics']['memoryUsage']['after']
            memory_heuristic_before = calculate_memory_heuristic(memory_before)
            memory_heuristic_after = calculate_memory_heuristic(memory_after)
            avg_memory_heuristic = (memory_heuristic_before + memory_heuristic_after) / 2
            memory_usages.append(avg_memory_heuristic / (1024 * 1024))
    
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#3498db', '#2ecc71', '#e74c3c']
    
    for i, runtime in enumerate(runtimes):
        ax.scatter(avg_times[i], memory_usages[i], color=colors[i], s=200, label=runtime)
        ax.annotate(runtime, 
                    (avg_times[i], memory_usages[i]),
                    xytext=(5, 5),
                    textcoords='offset points')
    
    ax.set_xlabel('Среднее время выполнения (мс)')
    ax.set_ylabel('Потребление памяти (МБ)')
    ax.set_title('Время выполнения vs Потребление памяти')
    ax.legend()
    
    # Добавляем описание и интерпретацию
    title = "Соотношение времени и памяти"
    description = """
    Эта диаграмма рассеяния показывает соотношение среднего времени выполнения (ось X) и потребления памяти (ось Y) 
    для каждого рантайма. Позволяет определить, какой рантайм обеспечивает оптимальный баланс между скоростью и использованием ресурсов.
    """
    interpretation = """
    1. Идеальное положение точки - левый нижний угол (быстрое выполнение + малое потребление памяти).
    2. Рантаймы в правом верхнем углу наименее эффективны (медленные + высокое потребление памяти).
    3. Рантаймы с близкими показателями по одной из осей можно сравнивать по другой метрике:
       - При примерно равном времени выполнения, предпочтительнее рантайм с меньшим потреблением памяти.
       - При сходном потреблении памяти, предпочтительнее более быстрый рантайм.
    4. Если точки образуют диагональную линию, это может указывать на типичный компромисс скорость/память.
    """
    fig = add_description_to_figure(fig, title, description, interpretation)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout()
    return fig, ax

# Функция для построения гистограммы времени выполнения конкретного рантайма
def plot_execution_time_histogram(runtime_data, runtime, save_path=None):
    """Строит гистограмму распределения времени выполнения для конкретного рантайма."""
    if not runtime_data:
        print(f"Данные {runtime} не найдены.")
        return None, None
    
    # Преобразуем из наносекунд в миллисекунды
    times_ms = [t / 1_000_000 for t in runtime_data['metrics']['executionTimes']]
    
    fig, ax = plt.subplots()
    sns.histplot(times_ms, kde=True, ax=ax, color='#3498db')
    
    ax.set_xlabel('Время выполнения (мс)')
    ax.set_ylabel('Частота')
    ax.set_title(f'Распределение времени выполнения {runtime}')
    
    # Добавление средней и медианной линий
    mean_time = runtime_data['metrics']['averageExecutionTime'] / 1_000_000
    median_time = runtime_data['statistics']['median'] / 1_000_000
    
    ax.axvline(mean_time, color='red', linestyle='--', label=f'Среднее: {mean_time:.2f} мс')
    ax.axvline(median_time, color='green', linestyle=':', label=f'Медиана: {median_time:.2f} мс')
    ax.legend()
    
    # Добавляем описание и интерпретацию
    title = f"Распределение времени выполнения: {runtime}"
    description = """
    Эта гистограмма показывает распределение времени выполнения для отдельного рантайма. 
    Высота каждого столбца указывает на число измерений в данном диапазоне времени. 
    Синяя кривая (KDE) показывает сглаженную оценку плотности распределения. 
    Вертикальные линии отмечают среднее значение (красная пунктирная) и медиану (зеленая точечная).
    """
    interpretation = """
    1. Узкое и высокое распределение (сконцентрированное вокруг одного пика) указывает на стабильную производительность.
    2. Широкое или многомодальное (с несколькими пиками) распределение указывает на нестабильность.
    3. Большой разрыв между средним и медианным значениями указывает на наличие выбросов:
       - Если среднее > медианы: есть выбросы в сторону больших значений.
       - Если медиана > среднего: есть выбросы в сторону меньших значений.
    4. В идеале распределение должно быть узким и симметричным, с близкими значениями среднего и медианы.
    """
    fig = add_description_to_figure(fig, title, description, interpretation)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout(pad=1.5)  # Увеличиваем отступы
    return fig, ax

# Функция для построения линейного графика времени выполнения по итерациям
def plot_execution_time_by_iteration(runtime_data, runtime, save_path=None):
    """Строит линейный график времени выполнения по итерациям для конкретного рантайма."""
    if not runtime_data:
        print(f"Данные {runtime} не найдены.")
        return None, None
    
    # Извлекаем времена по итерациям
    detailed_metrics = runtime_data.get('detailedIterationMetrics', [])
    iterations = []
    exec_times = []
    
    for i, metric in enumerate(detailed_metrics, 1):
        iterations.append(i)
        # Преобразуем в миллисекунды
        exec_times.append(metric['executionTime'] / 1_000_000)
    
    fig, ax = plt.subplots()
    ax.plot(iterations, exec_times, marker='o', linestyle='-', color='#3498db')
    
    # Добавляем скользящее среднее для тренда
    window_size = min(5, len(exec_times))  # Размер окна для скользящего среднего
    if window_size > 1:
        rolling_mean = pd.Series(exec_times).rolling(window=window_size).mean()
        ax.plot(iterations, rolling_mean, color='red', linestyle='--', 
                label=f'Скользящее среднее (окно={window_size})')
    
    ax.set_xlabel('Итерация')
    ax.set_ylabel('Время выполнения (мс)')
    ax.set_title(f'Время выполнения {runtime} по итерациям')
    ax.grid(True, alpha=0.3)
    
    if window_size > 1:
        ax.legend()
    
    # Добавляем описание и интерпретацию
    title = f"Время выполнения по итерациям: {runtime}"
    description = """
    Этот график показывает время выполнения каждой итерации тестового алгоритма, отображая изменение производительности
    в течение всего процесса тестирования. Синяя линия с маркерами показывает время каждой итерации, 
    а красная пунктирная линия - скользящее среднее, которое позволяет увидеть тренд.
    """
    interpretation = """
    1. Горизонтальная линия указывает на стабильную производительность на протяжении всех итераций.
    2. Убывающая линия в начале может указывать на эффект JIT-компиляции или прогрев кэша.
    3. Растущая линия может указывать на накопление негативных эффектов (например, сборка мусора не успевает).
    4. Периодические скачки могут указывать на фоновые процессы (например, сборка мусора).
    5. Изолированные пики могут быть вызваны внешними факторами (например, другие процессы в системе).
    """
    fig = add_description_to_figure(fig, title, description, interpretation)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout(pad=1.5)  # Увеличиваем отступы
    return fig, ax

# Функция для построения графика использования памяти по итерациям
def plot_memory_usage_by_iteration(runtime_data, runtime, save_path=None):
    """Строит график использования памяти heapUsed по итерациям для конкретного рантайма."""
    if not runtime_data:
        print(f"Данные {runtime} не найдены.")
        return None, None
    
    # Извлекаем данные использования памяти
    detailed_metrics = runtime_data.get('detailedIterationMetrics', [])
    iterations = []
    heap_used_before = []
    heap_used_after = []
    
    for i, metric in enumerate(detailed_metrics, 1):
        iterations.append(i)
        # Преобразуем в МБ для удобства восприятия
        heap_used_before.append(metric['memory']['before']['heapUsed'] / (1024 * 1024))
        heap_used_after.append(metric['memory']['after']['heapUsed'] / (1024 * 1024))
    
    fig, ax = plt.subplots()
    ax.plot(iterations, heap_used_before, marker='o', linestyle='-', 
            color='#3498db', label='До выполнения')
    ax.plot(iterations, heap_used_after, marker='x', linestyle='-', 
            color='#e74c3c', label='После выполнения')
    
    ax.set_xlabel('Итерация')
    ax.set_ylabel('Использование кучи (МБ)')
    ax.set_title(f'Использование памяти {runtime} по итерациям')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Добавляем описание и интерпретацию
    title = f"Использование памяти по итерациям: {runtime}"
    description = """
    Этот график показывает потребление памяти (JavaScript heap) для каждой итерации, измеренное до и после выполнения тестового алгоритма. 
    Синяя линия с маркерами (о) показывает использование памяти до выполнения алгоритма, 
    а красная линия с маркерами (x) - после выполнения.
    """
    interpretation = """
    1. Разница между красной и синей линиями показывает потребление памяти конкретно алгоритмом.
    2. Постепенный рост обеих линий может указывать на утечку памяти или недостаточную эффективность сборки мусора.
    3. Периодические падения могут указывать на срабатывание сборщика мусора.
    4. Стабильное плато указывает на хорошую память рантайма и отсутствие утечек.
    5. Большие скачки могут указывать на неэффективное управление памятью.
    """
    fig = add_description_to_figure(fig, title, description, interpretation)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout(pad=1.5)  # Увеличиваем отступы
    return fig, ax

# Функция для построения графика статистики времени выполнения
def plot_execution_time_statistics(runtime_data, runtime, save_path=None):
    """Строит столбчатую диаграмму со статистикой времени выполнения для конкретного рантайма."""
    if not runtime_data:
        print(f"Данные {runtime} не найдены.")
        return None, None
    
    # Извлекаем статистику
    stats = runtime_data['statistics']
    
    # Преобразуем в миллисекунды
    mean = stats['mean'] / 1_000_000
    median = stats['median'] / 1_000_000
    p95 = stats['p95'] / 1_000_000
    p99 = stats['p99'] / 1_000_000
    
    # Создаем данные для графика
    stat_names = ['Среднее', 'Медиана', 'P95', 'P99']
    stat_values = [mean, median, p95, p99]
    
    fig, ax = plt.subplots()
    bars = ax.bar(stat_names, stat_values, color=['#3498db', '#2ecc71', '#f1c40f', '#e74c3c'])
    
    # Добавляем значения над столбцами
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # смещение
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    ax.set_ylabel('Время (мс)')
    ax.set_title(f'Статистика времени выполнения {runtime}')
    
    # Добавляем описание и интерпретацию
    title = f"Статистические показатели времени выполнения: {runtime}"
    description = """
    Эта диаграмма показывает ключевые статистические показатели времени выполнения для рантайма:
    - Среднее: арифметическое среднее всех измерений
    - Медиана: значение, делящее выборку пополам (50-й процентиль)
    - P95: 95-й процентиль - значение, ниже которого находятся 95% всех измерений
    - P99: 99-й процентиль - значение, ниже которого находятся 99% всех измерений
    """
    interpretation = """
    1. Среднее vs Медиана: 
       - При близких значениях: распределение симметричное.
       - Если среднее > медианы: распределение имеет выбросы в сторону высоких значений.
       - Если медиана > среднего: распределение имеет выбросы в сторону низких значений.
    
    2. P95 и P99 показывают "наихудший случай" производительности:
       - Большой разрыв между медианой и P95/P99 указывает на нестабильность.
       - Близкие значения указывают на стабильную производительность.
    
    3. Для критических систем часто важнее P95/P99, чем среднее или медиана, т.к. они характеризуют
       производительность в неблагоприятных условиях.
    """
    fig = add_description_to_figure(fig, title, description, interpretation)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout(pad=1.5)  # Увеличиваем отступы
    return fig, ax

def analyze_runtime(runtime, output_dir, results_dir='results', experiment_type='fibonacci_recursive'):
    """Анализирует и создает графики для конкретного рантайма."""
    # Создаем директорию для графиков, если она не существует
    runtime_output_dir = os.path.join(output_dir, runtime)
    os.makedirs(runtime_output_dir, exist_ok=True)
    
    # Загружаем результаты для выбранного рантайма
    runtime_data = load_runtime_benchmark_results(runtime, results_dir, experiment_type)
    
    if not runtime_data:
        print(f"Ошибка: Данные для {runtime} не найдены")
        return
    
    # Строим и сохраняем графики
    plot_execution_time_histogram(runtime_data, runtime, 
                                save_path=os.path.join(runtime_output_dir, f'execution_time_histogram.png'))
    
    plot_execution_time_by_iteration(runtime_data, runtime, 
                                   save_path=os.path.join(runtime_output_dir, f'execution_time_by_iteration.png'))
    
    plot_memory_usage_by_iteration(runtime_data, runtime, 
                                save_path=os.path.join(runtime_output_dir, f'memory_usage_by_iteration.png'))
    
    plot_execution_time_statistics(runtime_data, runtime, 
                                 save_path=os.path.join(runtime_output_dir, f'execution_time_statistics.png'))
    
    print(f"Анализ для {runtime} завершен. Графики сохранены в директории:", runtime_output_dir)

def main():
    # Создаем директорию для графиков, если она не существует
    output_dir = 'analysis/computational/plots'
    os.makedirs(output_dir, exist_ok=True)
    
    # Загружаем результаты
    results = load_benchmark_results()
    
    # Строим и сохраняем общие графики
    plot_average_execution_times(results, 
                                save_path=os.path.join(output_dir, 'avg_execution_times.png'))
    
    plot_execution_time_boxplot(results, 
                               save_path=os.path.join(output_dir, 'execution_time_boxplot.png'))
    
    plot_memory_usage(results, 
                     save_path=os.path.join(output_dir, 'memory_usage.png'))
    
    plot_time_vs_memory(results, 
                       save_path=os.path.join(output_dir, 'time_vs_memory.png'))
    
    # Анализируем каждый рантайм отдельно
    runtimes = ['node', 'deno', 'bun']
    for runtime in runtimes:
        analyze_runtime(runtime, output_dir)
    
    print("Анализ завершен. Графики сохранены в директории:", output_dir)

if __name__ == "__main__":
    main() 