#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

# Настройка стилей
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.2)

# Константы
RUNTIME_COLORS = {
    'node': '#43A047',  # Более насыщенный зеленый для Node.js
    'deno': '#00BCD4',  # Яркий бирюзовый для Deno
    'bun': '#FFC107'    # Более яркий янтарный для Bun
}

# Фиксированный порядок отображения рантаймов
RUNTIME_ORDER = ['node', 'deno', 'bun']

BENCHMARK_TYPES = {
    'fibonacci_recursive_n40': 'Рекурсивный Фибоначчи (n=40)',
    'sorting_quicksort_size10000': 'QuickSort (n=10000)',
    'matrix_naive_size250': 'Умножение матриц (250x250)',
    'json_parse-stringify_size1000': 'JSON parse/stringify (1000)'
}

OUTPUT_DIRS = {
    'fibonacci_recursive_n40': 'fibonacci_recursive',
    'sorting_quicksort_size10000': 'sorting_quicksort',
    'matrix_naive_size250': 'matrix_naive',
    'json_parse-stringify_size1000': 'json_parse_stringify'
}

def load_benchmark_data(results_dir='results'):
    """Загружает все данные бенчмарков из JSON файлов"""
    data = []
    
    # Получаем список всех JSON файлов
    json_files = glob.glob(os.path.join(results_dir, '*.json'))
    
    for file_path in json_files:
        with open(file_path, 'r') as f:
            benchmark_data = json.load(f)
            
        # Извлекаем ключевую информацию
        runtime = benchmark_data['runtime']
        experiment = benchmark_data['experiment']
        
        # Преобразуем время выполнения из наносекунд в миллисекунды
        execution_times_ms = [t / 1e6 for t in benchmark_data['metrics']['executionTimes']]
        
        # Статистика
        statistics = benchmark_data['statistics']
        mean_ms = statistics['mean'] / 1e6
        median_ms = statistics['median'] / 1e6
        stddev_ms = statistics['stdDev'] / 1e6
        p95_ms = statistics['p95'] / 1e6
        p99_ms = statistics['p99'] / 1e6
        
        # Детальная информация по итерациям
        iterations_data = []
        for idx, iteration in enumerate(benchmark_data.get('detailedIterationMetrics', [])):
            iter_time_ms = iteration['executionTime'] / 1e6
            
            # Извлекаем информацию о памяти
            memory_before = iteration['memory']['before'].get('heapUsed', 0)
            memory_after = iteration['memory']['after'].get('heapUsed', 0)
            memory_diff = iteration['memory']['diff'].get('heapUsed', 0)
            
            iterations_data.append({
                'iteration': idx + 1,
                'execution_time_ms': iter_time_ms,
                'memory_before': memory_before,
                'memory_after': memory_after,
                'memory_diff': memory_diff,
                'gc_likely': memory_diff < 0
            })
        
        # Добавляем информацию в общий список
        data.append({
            'runtime': runtime,
            'experiment': experiment,
            'execution_times_ms': execution_times_ms,
            'mean_ms': mean_ms,
            'median_ms': median_ms,
            'stddev_ms': stddev_ms,
            'cv': (stddev_ms / mean_ms) * 100,  # Коэффициент вариации
            'p95_ms': p95_ms,
            'p99_ms': p99_ms,
            'iterations': iterations_data,
            'file_path': file_path
        })
    
    return data

def create_distribution_plot(data, output_dir):
    """Создает распределение производительности (боксплоты и скрипичные диаграммы)"""
    # Группируем данные по типу бенчмарка
    benchmark_types = set(item['experiment'] for item in data)
    
    # Создаем фигуру
    fig, axes = plt.subplots(1, len(benchmark_types), figsize=(16, 10), sharey=False)
    if len(benchmark_types) == 1:
        axes = [axes]
    
    for i, benchmark_type in enumerate(sorted(benchmark_types)):
        # Фильтруем данные для текущего типа бенчмарка
        benchmark_data = [item for item in data if item['experiment'] == benchmark_type]
        
        # Сортируем данные по заданному порядку рантаймов
        benchmark_data_sorted = []
        for runtime in RUNTIME_ORDER:
            for item in benchmark_data:
                if item['runtime'] == runtime:
                    benchmark_data_sorted.append(item)
        
        # Подготавливаем данные для визуализации
        plot_data = []
        labels = []
        colors = []
        
        for item in benchmark_data_sorted:
            plot_data.append(item['execution_times_ms'])
            labels.append(item['runtime'])
            colors.append(RUNTIME_COLORS[item['runtime']])
        
        # Проверяем, нужно ли использовать логарифмическую шкалу
        max_time = max(max(times) for times in plot_data)
        min_time = min(min(times) for times in plot_data)
        log_scale = max_time / min_time > 5
        
        # Создаем скрипичную диаграмму
        parts = axes[i].violinplot(plot_data, showmeans=False, showmedians=True)
        
        # Настраиваем цвета для скрипичных диаграмм
        for j, pc in enumerate(parts['bodies']):
            pc.set_facecolor(colors[j])
            pc.set_alpha(0.7)
        
        # Добавляем точки с джиттером
        for j, d in enumerate(plot_data):
            pos = j + 1
            axes[i].scatter([pos + 0.1 * np.random.randn(len(d))], [d], 
                         alpha=0.4, s=5, c=colors[j])
        
        # Улучшенные подписи статистик под графиком (вместо аннотаций внутри графика)
        runtime_info = []
        for j, item in enumerate(benchmark_data_sorted):
            runtime_info.append(f"{item['runtime']}\nmdn: {item['median_ms']:.2f}ms\np95: {item['p95_ms']:.2f}ms\np99: {item['p99_ms']:.2f}ms")
        
        # Обновляем подписи оси X с дополнительной информацией
        axes[i].set_xticks(np.arange(1, len(labels) + 1))
        axes[i].set_xticklabels(runtime_info, fontsize=9)
        
        # Настройка осей
        axes[i].set_title(BENCHMARK_TYPES.get(benchmark_type, benchmark_type), fontsize=14, fontweight='bold')
        axes[i].set_ylabel('Время (мс)', fontsize=12)
        
        if log_scale:
            axes[i].set_yscale('log')
    
    # Глобальный заголовок
    fig.suptitle('Распределение времени выполнения по рантаймам', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Оставляем место для общего заголовка
    plt.savefig(os.path.join(output_dir, '1_performance_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_stability_plot(data, output_dir):
    """Создает график стабильности производительности"""
    # Группируем данные по типу бенчмарка
    benchmark_types = set(item['experiment'] for item in data)
    
    # Создаем фигуру
    fig, axes = plt.subplots(len(benchmark_types), 1, figsize=(12, 5 * len(benchmark_types)))
    if len(benchmark_types) == 1:
        axes = [axes]
    
    for i, benchmark_type in enumerate(sorted(benchmark_types)):
        # Фильтруем данные для текущего типа бенчмарка
        benchmark_data = [item for item in data if item['experiment'] == benchmark_type]
        
        # Создаем словарь для сортировки данных по заданному порядку рантаймов
        runtime_data_map = {}
        for item in benchmark_data:
            runtime_data_map[item['runtime']] = item
        
        # Обрабатываем рантаймы в заданном порядке
        for runtime in RUNTIME_ORDER:
            if runtime in runtime_data_map:
                item = runtime_data_map[runtime]
                color = RUNTIME_COLORS[runtime]
                
                # Создаем DataFrame для текущего рантайма
                iteration_df = pd.DataFrame([
                    {
                        'iteration': i+1,
                        'execution_time_ms': exec_time
                    }
                    for i, exec_time in enumerate(item['execution_times_ms'])
                ])
                
                # Рисуем линию
                axes[i].plot(iteration_df['iteration'], iteration_df['execution_time_ms'], 
                          marker='o', linestyle='-', label=runtime, color=color, alpha=0.8)
                
                # Добавляем медиану
                axes[i].axhline(y=item['median_ms'], color=color, linestyle='--', alpha=0.6)
                
                # Добавляем p25 и p75 как прозрачную область
                p25 = np.percentile(item['execution_times_ms'], 25)
                p75 = np.percentile(item['execution_times_ms'], 75)
                axes[i].fill_between(iteration_df['iteration'], 
                                  [p25] * len(iteration_df), 
                                  [p75] * len(iteration_df), 
                                  color=color, alpha=0.2)
        
        # Настройка осей
        axes[i].set_title(BENCHMARK_TYPES.get(benchmark_type, benchmark_type), fontsize=14, fontweight='bold')
        axes[i].set_xlabel('Номер итерации', fontsize=12)
        axes[i].set_ylabel('Время выполнения (мс)', fontsize=12)
        axes[i].legend(title='Рантайм', fontsize=10)
        axes[i].grid(True, alpha=0.3)
    
    # Глобальный заголовок
    fig.suptitle('Стабильность производительности рантаймов по итерациям', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Оставляем место для общего заголовка
    plt.savefig(os.path.join(output_dir, '2_performance_stability.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_gc_performance_plot(data, output_dir):
    """Создает график для анализа взаимосвязи GC и производительности"""
    # Группируем данные по типу бенчмарка
    benchmark_types = set(item['experiment'] for item in data)
    
    for benchmark_type in sorted(benchmark_types):
        # Фильтруем данные для текущего типа бенчмарка
        benchmark_data = [item for item in data if item['experiment'] == benchmark_type]
        
        # Создаем словарь для сортировки данных по заданному порядку рантаймов
        runtime_data_map = {}
        for item in benchmark_data:
            runtime_data_map[item['runtime']] = item
        
        # Создаем фигуру
        plt.figure(figsize=(12, 8))
        
        # Обрабатываем рантаймы в заданном порядке
        for runtime in RUNTIME_ORDER:
            if runtime in runtime_data_map:
                item = runtime_data_map[runtime]
                color = RUNTIME_COLORS[runtime]
                
                # Создаем DataFrame для итераций
                iter_data = []
                for iter_info in item['iterations']:
                    iter_data.append({
                        'iteration': iter_info['iteration'],
                        'execution_time_ms': iter_info['execution_time_ms'],
                        'memory_diff': iter_info['memory_diff'],
                        'gc_likely': iter_info['gc_likely'],
                        'runtime': runtime
                    })
                
                iter_df = pd.DataFrame(iter_data)
                
                # Рисуем точки
                plt.scatter(
                    iter_df['memory_diff'], 
                    iter_df['execution_time_ms'],
                    s=iter_df['iteration'] * 2,  # Размер точки зависит от номера итерации
                    c=color,
                    alpha=0.7,
                    label=runtime
                )
                
                # Выделяем точки с вероятным GC
                gc_points = iter_df[iter_df['gc_likely']]
                if not gc_points.empty:
                    plt.scatter(
                        gc_points['memory_diff'], 
                        gc_points['execution_time_ms'],
                        s=gc_points['iteration'] * 2,
                        edgecolor='red',
                        facecolor='none',
                        linewidth=2
                    )
                
                # Добавляем линию регрессии
                if len(iter_df) > 1:
                    # Проверяем, что значения memory_diff не все одинаковые
                    if iter_df['memory_diff'].nunique() > 1:
                        slope, intercept, r_value, p_value, std_err = stats.linregress(
                            iter_df['memory_diff'], iter_df['execution_time_ms']
                        )
                        x_range = np.linspace(iter_df['memory_diff'].min(), iter_df['memory_diff'].max(), 100)
                        plt.plot(x_range, intercept + slope * x_range, color=color, linestyle='--', alpha=0.7)
        
        # Настройка осей и заголовков
        plt.title(f"Взаимосвязь GC и производительности - {BENCHMARK_TYPES.get(benchmark_type, benchmark_type)}", 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Изменение используемой памяти (байты)', fontsize=12)
        plt.ylabel('Время выполнения (мс)', fontsize=12)
        plt.legend(title='Рантайм', fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # Сохраняем график
        output_subdir = os.path.join(output_dir, OUTPUT_DIRS.get(benchmark_type, benchmark_type))
        plt.savefig(os.path.join(output_subdir, '3_gc_performance.png'), dpi=300, bbox_inches='tight')
        plt.close()

def create_performance_heatmap(data, output_dir):
    """Создает тепловую карту производительности"""
    # Группируем данные по типу бенчмарка
    all_benchmark_data = {}
    
    for item in data:
        benchmark_type = item['experiment']
        runtime = item['runtime']
        
        if benchmark_type not in all_benchmark_data:
            all_benchmark_data[benchmark_type] = {}
        
        all_benchmark_data[benchmark_type][runtime] = {
            'mean': item['mean_ms'],
            'median': item['median_ms'],
            'stddev': item['stddev_ms'],
            'cv': item['cv'],
            'p95': item['p95_ms'],
            'p99': item['p99_ms']
        }
    
    # Создаем dataframe для тепловой карты
    metrics = ['mean', 'median', 'stddev', 'cv', 'p95', 'p99']
    metric_names = ['Среднее (мс)', 'Медиана (мс)', 'СКО (мс)', 'Коэф. вариации (%)', 'p95 (мс)', 'p99 (мс)']
    
    for benchmark_type, runtime_data in all_benchmark_data.items():
        # Нормализуем данные относительно лучшего результата для каждой метрики
        # (для всех метрик, кроме cv, меньше = лучше)
        normalized_data = {runtime: {} for runtime in runtime_data.keys()}
        
        for metric in metrics:
            best_value = min(rd[metric] for rd in runtime_data.values())
            if metric == 'cv':
                best_value = min(rd[metric] for rd in runtime_data.values())
            
            for runtime, rd in runtime_data.items():
                if best_value == 0:
                    normalized_data[runtime][metric] = 1.0
                else:
                    normalized_data[runtime][metric] = rd[metric] / best_value
        
        # Создаем DataFrame в заданном порядке рантаймов
        df_data = []
        for runtime in RUNTIME_ORDER:
            if runtime in runtime_data:
                row = [runtime]
                for metric in metrics:
                    row.append(runtime_data[runtime][metric])
                df_data.append(row)
        
        df = pd.DataFrame(df_data, columns=['Runtime'] + metric_names)
        df.set_index('Runtime', inplace=True)
        
        # Создаем тепловую карту
        plt.figure(figsize=(12, 6))
        
        # Используем улучшенную цветовую схему для тепловой карты
        cmap = "RdYlGn_r"  # Стандартное распределение от зеленого к красному
        ax = sns.heatmap(df, annot=True, fmt=".2f", cmap=cmap, linewidths=0.5, annot_kws={"size": 10})
        
        # Увеличиваем размер текста для меток осей
        plt.yticks(fontsize=11)
        plt.xticks(fontsize=10, rotation=30, ha='right')
        
        # Настройка осей и заголовка
        plt.title(f"Сводная таблица производительности - {BENCHMARK_TYPES.get(benchmark_type, benchmark_type)}", 
                fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Сохраняем график
        output_subdir = os.path.join(output_dir, OUTPUT_DIRS.get(benchmark_type, benchmark_type))
        plt.savefig(os.path.join(output_subdir, '4_performance_heatmap.png'), dpi=300, bbox_inches='tight')
        plt.close()

def create_radar_plot(data, output_dir):
    """Создает радарный график для сравнения профилей производительности"""
    # Группируем данные по типу бенчмарка
    all_benchmark_data = {}
    
    for item in data:
        benchmark_type = item['experiment']
        runtime = item['runtime']
        
        if benchmark_type not in all_benchmark_data:
            all_benchmark_data[benchmark_type] = {}
        
        all_benchmark_data[benchmark_type][runtime] = {
            'mean': item['mean_ms'],
            'median': item['median_ms'],
            'stddev': item['stddev_ms'],
            'p95': item['p95_ms'],
            'p99': item['p99_ms']
        }
    
    for benchmark_type, runtime_data in all_benchmark_data.items():
        # Нормализуем данные
        metrics = ['mean', 'median', 'stddev', 'p95', 'p99']
        metric_names = ['Среднее', 'Медиана', 'СКО', 'p95', 'p99']
        
        normalized_data = {runtime: {} for runtime in runtime_data.keys()}
        
        for metric in metrics:
            best_value = min(rd[metric] for rd in runtime_data.values())
            for runtime, rd in runtime_data.items():
                if best_value == 0:
                    normalized_data[runtime][metric] = 1.0
                else:
                    normalized_data[runtime][metric] = rd[metric] / best_value
        
        # Создаем радарный график с улучшенными цветами и в заданном порядке рантаймов
        fig = go.Figure()
        
        for runtime in RUNTIME_ORDER:
            if runtime in runtime_data:
                # Замыкаем график, добавляя первую точку в конце
                values = [normalized_data[runtime][metric] for metric in metrics] + [normalized_data[runtime][metrics[0]]]
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=metric_names + [metric_names[0]],
                    fill='toself',
                    name=runtime,
                    line=dict(color=RUNTIME_COLORS.get(runtime, '#000000'), width=2),
                    fillcolor=RUNTIME_COLORS.get(runtime, '#000000'),
                    opacity=0.7
                ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0.9, max(max(normalized_data[runtime][metric] for metric in metrics) for runtime in runtime_data.keys()) * 1.1]
                )
            ),
            title=dict(
                text=f"Сравнительный анализ профилей - {BENCHMARK_TYPES.get(benchmark_type, benchmark_type)}",
                font=dict(size=16)
            ),
            legend=dict(
                title="Рантайм", 
                font=dict(size=12)
            ),
            width=900,
            height=700
        )
        
        # Сохраняем график
        output_subdir = os.path.join(output_dir, OUTPUT_DIRS.get(benchmark_type, benchmark_type))
        fig.write_image(os.path.join(output_subdir, '5_radar_plot.png'), width=900, height=700)

def main():
    # Загружаем данные бенчмарков
    benchmark_data = load_benchmark_data()
    
    # Группируем данные по эксперименту
    experiment_groups = {}
    for item in benchmark_data:
        experiment = item['experiment']
        if experiment not in experiment_groups:
            experiment_groups[experiment] = []
        experiment_groups[experiment].append(item)
    
    # Основной каталог для результатов
    output_dir = 'analysis/computational/results'
    
    # Создаем визуализации для каждого типа бенчмарка
    for experiment, exp_data in experiment_groups.items():
        # Создаем каталог для результатов этого эксперимента, если он еще не существует
        experiment_dir = os.path.join(output_dir, OUTPUT_DIRS.get(experiment, experiment))
        os.makedirs(experiment_dir, exist_ok=True)
        
        # Создаем все визуализации
        create_gc_performance_plot(exp_data, output_dir)
        create_performance_heatmap(exp_data, output_dir)
        create_radar_plot(exp_data, output_dir)
        
    # Создаем общие визуализации
    create_distribution_plot(benchmark_data, output_dir)
    create_stability_plot(benchmark_data, output_dir)
    
    print("Визуализации созданы в директории:", output_dir)

if __name__ == "__main__":
    main() 