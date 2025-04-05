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

# Функция для загрузки результатов тестирования только для Node.js
def load_node_benchmark_results(results_dir='results', experiment_type='fibonacci_recursive'):
    """Загружает результаты тестов производительности Node.js из директории."""
    node_results = None
    
    for filename in os.listdir(results_dir):
        if experiment_type in filename and 'node' in filename:
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'r') as f:
                node_results = json.load(f)
                if node_results.get('runtime') != 'node':
                    node_results = None
            if node_results:
                break  # Нашли результаты для Node.js
    
    return node_results

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

# Функция для построения гистограммы времени выполнения
def plot_execution_time_histogram(node_data, save_path=None):
    """Строит гистограмму распределения времени выполнения."""
    if not node_data:
        print("Данные Node.js не найдены.")
        return None, None
    
    # Преобразуем из наносекунд в миллисекунды
    times_ms = [t / 1_000_000 for t in node_data['metrics']['executionTimes']]
    
    fig, ax = plt.subplots()
    sns.histplot(times_ms, kde=True, ax=ax, color='#3498db')
    
    ax.set_xlabel('Время выполнения (мс)')
    ax.set_ylabel('Частота')
    ax.set_title('Распределение времени выполнения Node.js')
    
    # Добавление средней и медианной линий
    mean_time = node_data['metrics']['averageExecutionTime'] / 1_000_000
    median_time = node_data['statistics']['median'] / 1_000_000
    
    ax.axvline(mean_time, color='red', linestyle='--', label=f'Среднее: {mean_time:.2f} мс')
    ax.axvline(median_time, color='green', linestyle=':', label=f'Медиана: {median_time:.2f} мс')
    ax.legend()
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout(pad=1.5)  # Увеличиваем отступы
    return fig, ax

# Функция для построения линейного графика времени выполнения по итерациям
def plot_execution_time_by_iteration(node_data, save_path=None):
    """Строит линейный график времени выполнения по итерациям."""
    if not node_data:
        print("Данные Node.js не найдены.")
        return None, None
    
    # Извлекаем времена по итерациям
    detailed_metrics = node_data.get('detailedIterationMetrics', [])
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
    ax.set_title('Время выполнения Node.js по итерациям')
    ax.grid(True, alpha=0.3)
    
    if window_size > 1:
        ax.legend()
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout(pad=1.5)  # Увеличиваем отступы
    return fig, ax

# Функция для построения графика использования памяти по итерациям
def plot_memory_usage_by_iteration(node_data, save_path=None):
    """Строит график использования памяти heapUsed по итерациям."""
    if not node_data:
        print("Данные Node.js не найдены.")
        return None, None
    
    # Извлекаем данные использования памяти
    detailed_metrics = node_data.get('detailedIterationMetrics', [])
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
    ax.set_title('Использование памяти Node.js по итерациям')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout(pad=1.5)  # Увеличиваем отступы
    return fig, ax

# Функция для построения графика статистики времени выполнения
def plot_execution_time_statistics(node_data, save_path=None):
    """Строит столбчатую диаграмму со статистикой времени выполнения."""
    if not node_data:
        print("Данные Node.js не найдены.")
        return None, None
    
    # Извлекаем статистику
    stats = node_data['statistics']
    
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
    ax.set_title('Статистика времени выполнения Node.js')
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout(pad=1.5)  # Увеличиваем отступы
    return fig, ax

def main():
    # Создаем директорию для графиков, если она не существует
    output_dir = 'analysis/computational/plots/node'
    os.makedirs(output_dir, exist_ok=True)
    
    # Загружаем результаты только для Node.js
    node_data = load_node_benchmark_results()
    
    if not node_data:
        print("Ошибка: Данные для Node.js не найдены")
        return
    
    # Строим и сохраняем графики
    plot_execution_time_histogram(node_data, 
                               save_path=os.path.join(output_dir, 'execution_time_histogram.png'))
    
    plot_execution_time_by_iteration(node_data, 
                                  save_path=os.path.join(output_dir, 'execution_time_by_iteration.png'))
    
    plot_memory_usage_by_iteration(node_data, 
                               save_path=os.path.join(output_dir, 'memory_usage_by_iteration.png'))
    
    plot_execution_time_statistics(node_data, 
                                save_path=os.path.join(output_dir, 'execution_time_statistics.png'))
    
    print("Анализ завершен. Графики сохранены в директории:", output_dir)

if __name__ == "__main__":
    main() 