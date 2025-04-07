#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для анализа результатов асинхронных бенчмарков JavaScript-рантаймов.
Читает JSON-файлы с результатами и генерирует визуализации для сравнения производительности.
"""

import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter
from datetime import datetime

# Настройки для графиков
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.2)
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.family'] = 'DejaVu Sans'

# Обновленная цветовая схема и порядок рантаймов
RUNTIME_COLORS = {
    'node': '#43A047',  # Более насыщенный зеленый для Node.js
    'deno': '#00BCD4',  # Яркий бирюзовый для Deno
    'bun': '#FFC107'    # Более яркий янтарный для Bun
}

# Фиксированный порядок отображения рантаймов
RUNTIME_ORDER = ['node', 'deno', 'bun']
RUNTIME_NAMES = {'node': 'Node.js', 'deno': 'Deno', 'bun': 'Bun'}

# Конфигурация директорий
RESULTS_DIR = 'results'
OUTPUT_DIR = 'analysis/async/results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def format_ms(x, pos):
    """Форматирование миллисекунд для графиков"""
    return f'{x:.1f} мс'

def format_rps(x, pos):
    """Форматирование запросов в секунду для графиков"""
    return f'{x:.0f}'

def load_benchmark_results(pattern='*_async_*.json'):
    """Загрузка результатов бенчмарков из JSON-файлов"""
    results = {}
    
    for filepath in glob.glob(os.path.join(RESULTS_DIR, pattern)):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            runtime = data.get('runtime')
            if runtime not in results:
                results[runtime] = []
                
            # Обработка каждой итерации
            for iteration in data.get('iterations', []):
                if iteration.get('success'):
                    # Извлекаем необходимые метрики
                    metrics = {
                        'timestamp': iteration.get('timestamp'),
                        'latency_avg': parse_time_to_ms(iteration.get('results', {}).get('latency', {}).get('avg', '0ms')),
                        'latency_stdev': parse_time_to_ms(iteration.get('results', {}).get('latency', {}).get('stdev', '0ms')),
                        'latency_max': parse_time_to_ms(iteration.get('results', {}).get('latency', {}).get('max', '0ms')),
                        'req_per_sec': float(iteration.get('results', {}).get('summary', {}).get('requests_per_sec', 0)),
                        'req_per_sec_avg': float(iteration.get('results', {}).get('requests_per_sec', {}).get('avg', 0)),
                        'req_per_sec_stdev': float(iteration.get('results', {}).get('requests_per_sec', {}).get('stdev', 0)),
                        'req_per_sec_max': float(iteration.get('results', {}).get('requests_per_sec', {}).get('max', 0)),
                        'total_requests': int(iteration.get('results', {}).get('summary', {}).get('total_requests', 0)),
                        'server_async_duration': float(iteration.get('results', {}).get('summary', {}).get('server_async_duration_ms', 0)),
                        'iteration': iteration.get('iteration')
                    }
                    results[runtime].append(metrics)
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка при чтении файла {filepath}: {e}")
    
    return results

def parse_time_to_ms(time_str):
    """Преобразует строку времени (например, '10.5ms' или '1.2s') в миллисекунды"""
    try:
        if not time_str or time_str == 'N/A':
            return 0.0
            
        if 'ms' in time_str:
            return float(time_str.replace('ms', ''))
        elif 's' in time_str:
            return float(time_str.replace('s', '')) * 1000
        else:
            return float(time_str)
    except (ValueError, TypeError):
        return 0.0

def calculate_aggregated_metrics(results):
    """Вычисляет агрегированные метрики по всем итерациям для каждого рантайма"""
    aggregated = {}
    
    for runtime, iterations in results.items():
        if not iterations:
            continue
            
        df = pd.DataFrame(iterations)
        
        aggregated[runtime] = {
            'latency_avg_mean': df['latency_avg'].mean(),
            'latency_avg_std': df['latency_avg'].std(),
            'req_per_sec_mean': df['req_per_sec'].mean(),
            'req_per_sec_std': df['req_per_sec'].std(),
            'server_async_duration_mean': df['server_async_duration'].mean(),
            'server_async_duration_std': df['server_async_duration'].std(),
            'iterations_count': len(iterations)
        }
    
    return aggregated

def plot_async_duration_comparison(aggregated_data, filename='1_async_duration_comparison.png'):
    """Создает график сравнения времени выполнения асинхронных задач"""
    # Сортировка рантаймов в соответствии с заданным порядком
    runtimes = []
    for rt in RUNTIME_ORDER:
        if rt in aggregated_data:
            runtimes.append(rt)
    
    means = [aggregated_data[rt]['server_async_duration_mean'] for rt in runtimes]
    stds = [aggregated_data[rt]['server_async_duration_std'] for rt in runtimes]
    
    nice_names = [RUNTIME_NAMES.get(rt, rt) for rt in runtimes]
    colors = [RUNTIME_COLORS.get(rt, 'gray') for rt in runtimes]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(nice_names, means, yerr=stds, capsize=10, color=colors, alpha=0.7)
    
    # Добавляем значения над барами
    for bar, val in zip(bars, means):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{val:.2f} мс', ha='center', va='bottom', fontsize=11)
    
    ax.set_ylabel('Время выполнения (мс)', fontsize=12)
    ax.set_title('Сравнение времени выполнения асинхронных задач', fontsize=14, fontweight='bold')
    ax.yaxis.set_major_formatter(FuncFormatter(format_ms))
    
    # Добавляем метку для источника данных
    plt.figtext(0.99, 0.01, 'Данные: async_benchmark', horizontalalignment='right', 
                fontsize=8, alpha=0.7)
    
    timestamp = datetime.now().strftime('%Y-%m-%d')
    plt.figtext(0.01, 0.01, f'Создано: {timestamp}', horizontalalignment='left', 
                fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()

def plot_requests_per_second(aggregated_data, filename='2_rps_comparison.png'):
    """Создает график сравнения количества запросов в секунду"""
    # Сортировка рантаймов в соответствии с заданным порядком
    runtimes = []
    for rt in RUNTIME_ORDER:
        if rt in aggregated_data:
            runtimes.append(rt)
    
    means = [aggregated_data[rt]['req_per_sec_mean'] for rt in runtimes]
    stds = [aggregated_data[rt]['req_per_sec_std'] for rt in runtimes]
    
    nice_names = [RUNTIME_NAMES.get(rt, rt) for rt in runtimes]
    colors = [RUNTIME_COLORS.get(rt, 'gray') for rt in runtimes]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(nice_names, means, yerr=stds, capsize=10, color=colors, alpha=0.7)
    
    # Добавляем значения над барами
    for bar, val in zip(bars, means):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{val:.1f}', ha='center', va='bottom', fontsize=11)
    
    ax.set_ylabel('Запросов в секунду (RPS)', fontsize=12)
    ax.set_title('Пропускная способность по рантаймам', fontsize=14, fontweight='bold')
    ax.yaxis.set_major_formatter(FuncFormatter(format_rps))
    
    # Добавляем метку для источника данных
    plt.figtext(0.99, 0.01, 'Данные: async_benchmark', horizontalalignment='right', 
                fontsize=8, alpha=0.7)
    
    timestamp = datetime.now().strftime('%Y-%m-%d')
    plt.figtext(0.01, 0.01, f'Создано: {timestamp}', horizontalalignment='left', 
                fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()

def plot_latency_comparison(results, filename='3_latency_comparison.png'):
    """Создает график сравнения латентности"""
    data = []
    
    # Сортировка данных согласно порядку рантаймов
    for runtime in RUNTIME_ORDER:
        if runtime in results:
            iterations = results[runtime]
            for iteration in iterations:
                data.append({
                    'Runtime': RUNTIME_NAMES.get(runtime, runtime),
                    'Latency (ms)': iteration['latency_avg'],
                    'Iteration': iteration['iteration']
                })
    
    df = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Определяем палитру цветов в соответствии с порядком рантаймов
    palette = {}
    for rt in RUNTIME_ORDER:
        if RUNTIME_NAMES.get(rt) in df['Runtime'].unique():
            palette[RUNTIME_NAMES.get(rt)] = RUNTIME_COLORS.get(rt)
    
    # Создаем box plot для латентности
    sns.boxplot(x='Runtime', y='Latency (ms)', data=df, 
                palette=palette,
                ax=ax, order=[RUNTIME_NAMES.get(rt) for rt in RUNTIME_ORDER if RUNTIME_NAMES.get(rt) in df['Runtime'].unique()])
    
    # Добавляем точки для каждой итерации
    sns.stripplot(x='Runtime', y='Latency (ms)', data=df, 
                 size=8, jitter=True, alpha=0.6, ax=ax, 
                 palette=palette,
                 order=[RUNTIME_NAMES.get(rt) for rt in RUNTIME_ORDER if RUNTIME_NAMES.get(rt) in df['Runtime'].unique()])
    
    ax.set_title('Сравнение латентности по рантаймам', fontsize=14, fontweight='bold')
    ax.set_ylabel('Среднее время отклика (мс)', fontsize=12)
    ax.set_xlabel('')
    
    # Форматирование оси Y
    ax.yaxis.set_major_formatter(FuncFormatter(format_ms))
    
    # Добавляем метку для источника данных
    plt.figtext(0.99, 0.01, 'Данные: async_benchmark', horizontalalignment='right', 
                fontsize=8, alpha=0.7)
    
    timestamp = datetime.now().strftime('%Y-%m-%d')
    plt.figtext(0.01, 0.01, f'Создано: {timestamp}', horizontalalignment='left', 
                fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()

def plot_stability_comparison(results, filename='4_performance_stability.png'):
    """Создает график стабильности производительности"""
    stability_data = []
    
    # Сортировка рантаймов в соответствии с заданным порядком
    for runtime in RUNTIME_ORDER:
        if runtime in results:
            iterations = results[runtime]
            if not iterations:
                continue
                
            df = pd.DataFrame(iterations)
            
            # Нормализация для сравнения разных метрик
            latency_coeff = df['latency_avg'].std() / df['latency_avg'].mean() if df['latency_avg'].mean() > 0 else 0
            rps_coeff = df['req_per_sec'].std() / df['req_per_sec'].mean() if df['req_per_sec'].mean() > 0 else 0
            async_duration_coeff = df['server_async_duration'].std() / df['server_async_duration'].mean() if df['server_async_duration'].mean() > 0 else 0
            
            stability_data.append({
                'Runtime': RUNTIME_NAMES.get(runtime, runtime),
                'Latency CV': latency_coeff * 100,  # Коэффициент вариации в процентах
                'RPS CV': rps_coeff * 100,
                'Async Duration CV': async_duration_coeff * 100
            })
    
    df_stability = pd.DataFrame(stability_data)
    
    # Преобразуем данные для визуализации
    df_melted = pd.melt(df_stability, id_vars=['Runtime'], 
                        value_vars=['Latency CV', 'RPS CV', 'Async Duration CV'],
                        var_name='Metric', value_name='Coefficient of Variation (%)')
    
    # Создаем график
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Используем barplot для сравнения коэффициентов вариации
    # Устанавливаем явный порядок для рантаймов
    runtime_order = [RUNTIME_NAMES.get(rt) for rt in RUNTIME_ORDER if RUNTIME_NAMES.get(rt) in df_melted['Runtime'].unique()]
    
    sns.barplot(x='Runtime', y='Coefficient of Variation (%)', hue='Metric', 
                data=df_melted, 
                palette={'Latency CV': '#00BCD4', 'RPS CV': '#43A047', 'Async Duration CV': '#FFC107'},
                ax=ax, order=runtime_order)
    
    # Добавляем заголовок и подписи осей
    ax.set_title('Стабильность производительности (меньше = лучше)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Коэффициент вариации (%)', fontsize=12)
    ax.set_xlabel('')
    
    # Добавляем легенду
    ax.legend(title='Метрика', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Добавляем метку для источника данных
    plt.figtext(0.99, 0.01, 'Данные: async_benchmark', horizontalalignment='right', 
                fontsize=8, alpha=0.7)
    
    timestamp = datetime.now().strftime('%Y-%m-%d')
    plt.figtext(0.01, 0.01, f'Создано: {timestamp}', horizontalalignment='left', 
                fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()

def plot_radar_chart(aggregated_data, filename='5_radar_performance.png'):
    """Создает радарную диаграмму для сравнения производительности"""
    # Сортировка рантаймов в соответствии с заданным порядком
    runtimes = []
    for rt in RUNTIME_ORDER:
        if rt in aggregated_data:
            runtimes.append(rt)
    
    if not runtimes:
        print("Нет данных для построения радарной диаграммы")
        return
    
    # Функция масштабированной нормализации
    def scaled_normalization(values, inverse=False, minimum_value=0.4):
        """
        Модифицированная min-max нормализация с минимальным порогом.
        
        Args:
            values: Список значений для нормализации
            inverse: Инвертировать значения (для метрик где меньше = лучше)
            minimum_value: Минимальное значение после нормализации (0..1)
        """
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:  # Если все значения одинаковые
            return [1.0 for _ in values]
            
        scaled = []
        for val in values:
            if inverse:
                # Для метрик "меньше=лучше", сразу инвертируем и нормализуем
                normalized = 1.0 - ((val - min_val) / (max_val - min_val))
            else:
                # Для метрик "больше=лучше", просто нормализуем
                normalized = (val - min_val) / (max_val - min_val)
            
            # Применяем масштабирование для минимального значения
            normalized = normalized * (1.0 - minimum_value) + minimum_value
            
            scaled.append(normalized)
            
        return scaled
    
    # Подготовка данных для радарной диаграммы
    metrics = {}
    original_values = {}
    
    print("\nОригинальные значения метрик:")
    
    # Собираем и выводим оригинальные значения
    for metric in ['latency_avg_mean', 'req_per_sec_mean', 'server_async_duration_mean']:
        values = [aggregated_data[rt][metric] for rt in runtimes]
        original_values[metric] = values
        
        metric_name = {
            'latency_avg_mean': 'Латентность (мс)',
            'req_per_sec_mean': 'RPS',
            'server_async_duration_mean': 'Время асинхронных операций (мс)'
        }.get(metric, metric)
        
        print(f"{metric_name}:")
        for rt, val in zip(runtimes, values):
            print(f"  {RUNTIME_NAMES.get(rt, rt)}: {val:.2f}")
    
    # Нормализуем значения
    for metric in ['latency_avg_mean', 'req_per_sec_mean', 'server_async_duration_mean']:
        values = original_values[metric]
        
        if metric in ['latency_avg_mean', 'server_async_duration_mean']:
            # Для латентности и времени выполнения меньше = лучше
            metrics[metric] = scaled_normalization(values, inverse=True)
        else:
            # Для RPS больше = лучше
            metrics[metric] = scaled_normalization(values, inverse=False)
    
    # Коэффициенты вариации (для стабильности)
    cv_original = {}
    
    # Вычисляем и выводим коэффициенты вариации
    print("\nКоэффициенты вариации (стабильность):")
    
    for metric in ['latency_avg_std', 'req_per_sec_std', 'server_async_duration_std']:
        cv_values = []
        for rt in runtimes:
            std_val = aggregated_data[rt][metric]
            mean_val = aggregated_data[rt][metric.replace('_std', '_mean')]
            # Коэффициент вариации = std/mean
            if mean_val > 0:
                cv = std_val / mean_val
            else:
                cv = 0
            cv_values.append(cv)
        
        cv_original[metric] = cv_values
        
        metric_name = {
            'latency_avg_std': 'Стабильность латентности (CV)',
            'req_per_sec_std': 'Стабильность RPS (CV)',
            'server_async_duration_std': 'Стабильность асинхр. операций (CV)'
        }.get(metric, metric)
        
        print(f"{metric_name}:")
        for rt, val in zip(runtimes, cv_values):
            print(f"  {RUNTIME_NAMES.get(rt, rt)}: {val:.4f}")
        
        # Нормализуем и инвертируем (меньше = лучше)
        metrics[f'{metric}_stability'] = scaled_normalization(cv_values, inverse=True)
    
    # Выводим нормализованные значения
    print("\nНормализованные значения для радарного графика:")
    for category, metric_key in [
        ('Скорость асинхронных операций', 'server_async_duration_mean'),
        ('Пропускная способность (RPS)', 'req_per_sec_mean'),
        ('Низкая латентность', 'latency_avg_mean'),
        ('Стабильность асинхронных операций', 'server_async_duration_std_stability'),
        ('Стабильность пропускной способности', 'req_per_sec_std_stability'),
        ('Стабильность латентности', 'latency_avg_std_stability')
    ]:
        print(f"{category}:")
        for rt, val in zip(runtimes, metrics[metric_key]):
            print(f"  {RUNTIME_NAMES.get(rt, rt)}: {val:.2f}")
    
    # Создаем радарную диаграмму
    categories = [
        'Скорость асинхронных операций',
        'Пропускная способность (RPS)',
        'Низкая латентность',
        'Стабильность асинхронных операций',
        'Стабильность пропускной способности',
        'Стабильность латентности'
    ]
    
    # Получаем значения для каждой категории
    values = []
    for rt_idx, rt in enumerate(runtimes):
        rt_values = [
            metrics['server_async_duration_mean'][rt_idx],
            metrics['req_per_sec_mean'][rt_idx],
            metrics['latency_avg_mean'][rt_idx],
            metrics['server_async_duration_std_stability'][rt_idx],
            metrics['req_per_sec_std_stability'][rt_idx],
            metrics['latency_avg_std_stability'][rt_idx]
        ]
        values.append(rt_values)
    
    # Количество категорий
    N = len(categories)
    
    # Вычисляем угол для каждой оси
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Замыкаем круг
    
    # Создаем фигуру
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
    
    # Рисуем каждый рантайм
    for i, rt in enumerate(runtimes):
        values[i] += values[i][:1]  # Замыкаем значения
        color = RUNTIME_COLORS.get(rt)
        ax.plot(angles, values[i], linewidth=2, linestyle='solid', label=RUNTIME_NAMES.get(rt, rt), color=color)
        ax.fill(angles, values[i], alpha=0.1, color=color)
    
    # Устанавливаем метки осей
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    
    # Добавляем заголовок
    plt.title('Сравнение производительности асинхронных операций', size=14, fontweight='bold', y=1.1)
    
    # Добавляем легенду
    plt.legend(loc='upper right', bbox_to_anchor=(0, 0.1))
    
    # Настраиваем сетку
    ax.set_rlabel_position(0)
    plt.yticks([0.4, 0.6, 0.8, 1.0], ["0.4", "0.6", "0.8", "1.0"], color="grey", size=8)
    plt.ylim(0, 1)
    
    # Добавляем метку для источника данных
    plt.figtext(0.99, 0.01, 'Данные: async_benchmark', horizontalalignment='right', 
                fontsize=8, alpha=0.7)
    
    timestamp = datetime.now().strftime('%Y-%m-%d')
    plt.figtext(0.01, 0.01, f'Создано: {timestamp}', horizontalalignment='left', 
                fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Основная функция для создания всех графиков"""
    print("Загрузка результатов асинхронных бенчмарков...")
    results = load_benchmark_results(pattern='*_async_*.json')
    
    if not results:
        print("Не найдено данных бенчмарков. Проверьте наличие файлов *_async_*.json в директории с результатами.")
        return
    
    print(f"Найдены данные для следующих рантаймов: {', '.join(results.keys())}")
    
    # Вычисляем агрегированные метрики
    aggregated_data = calculate_aggregated_metrics(results)
    
    # Создаем графики
    print("Создание графиков...")
    
    plot_async_duration_comparison(aggregated_data)
    print("График времени выполнения асинхронных задач создан")
    
    plot_requests_per_second(aggregated_data)
    print("График пропускной способности создан")
    
    plot_latency_comparison(results)
    print("График латентности создан")
    
    plot_stability_comparison(results)
    print("График стабильности производительности создан")
    
    plot_radar_chart(aggregated_data)
    print("Радарная диаграмма создана")
    
    print(f"Все графики сохранены в директории {OUTPUT_DIR}")

if __name__ == "__main__":
    main() 