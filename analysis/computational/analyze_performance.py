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
sns.set_style("whitegrid")

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
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
    
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
    
    # Установка цветов для boxplot
    colors = ['#3498db', '#2ecc71', '#e74c3c']
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
    
    ax.set_ylabel('Время выполнения (мс)')
    ax.set_title('Распределение времени выполнения по рантаймам')
    
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
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
    
    plt.tight_layout()
    return fig, ax

def main():
    # Создаем директорию для графиков, если она не существует
    output_dir = 'analysis/computational/plots'
    os.makedirs(output_dir, exist_ok=True)
    
    # Загружаем результаты
    results = load_benchmark_results()
    
    # Строим и сохраняем графики
    plot_average_execution_times(results, 
                                save_path=os.path.join(output_dir, 'avg_execution_times.png'))
    
    plot_execution_time_boxplot(results, 
                               save_path=os.path.join(output_dir, 'execution_time_boxplot.png'))
    
    plot_memory_usage(results, 
                     save_path=os.path.join(output_dir, 'memory_usage.png'))
    
    plot_time_vs_memory(results, 
                       save_path=os.path.join(output_dir, 'time_vs_memory.png'))
    
    print("Анализ завершен. Графики сохранены в директории:", output_dir)

if __name__ == "__main__":
    main() 