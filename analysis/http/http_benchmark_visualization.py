#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import glob
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec
import matplotlib as mpl
from matplotlib.ticker import ScalarFormatter

# Настройка стилей
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.2)

# Константы
RUNTIME_COLORS = {
    'node': '#43A047',  # Зеленый для Node.js
    'deno': '#00BCD4',  # Бирюзовый для Deno
    'bun': '#FFC107'    # Янтарный для Bun
}

# Фиксированный порядок отображения рантаймов
RUNTIME_ORDER = ['node', 'deno', 'bun']

# Русские названия рантаймов для отображения на графиках
RUNTIME_NAMES_RU = {
    'node': 'Node.js',
    'deno': 'Deno',
    'bun': 'Bun'
}

def load_http_benchmark_data(results_dir='results/http'):
    """Загружает данные HTTP бенчмарков из JSON файлов"""
    data = []
    
    # Получаем список всех JSON файлов с HTTP бенчмарками
    json_files = glob.glob(os.path.join(results_dir, '*http*.json'))
    
    for file_path in json_files:
        with open(file_path, 'r') as f:
            benchmark_data = json.load(f)
            
        # Извлекаем ключевую информацию
        runtime = benchmark_data['runtime']
        timestamp = benchmark_data['timestamp']
        configuration = benchmark_data['configuration']
        iterations = benchmark_data['iterations']
        
        # Для каждой итерации извлекаем метрики
        iteration_metrics = []
        for iteration_data in iterations:
            iteration_num = iteration_data['iteration']
            results = iteration_data['results']
            
            # Преобразуем строки с ms в числовые значения
            latency_avg = float(re.sub(r'[^\d.]', '', results['latency']['avg']))
            latency_stdev = float(re.sub(r'[^\d.]', '', results['latency']['stdev']))
            latency_max = float(re.sub(r'[^\d.]', '', results['latency']['max']))
            
            rps_avg = results['requests_per_sec']['avg']
            rps_stdev = results['requests_per_sec']['stdev']
            rps_max = results['requests_per_sec']['max']
            
            summary_rps = results['summary']['requests_per_sec']
            
            iteration_metrics.append({
                'iteration': iteration_num,
                'latency_avg': latency_avg,
                'latency_stdev': latency_stdev,
                'latency_max': latency_max,
                'rps_avg': rps_avg,
                'rps_stdev': rps_stdev,
                'rps_max': rps_max,
                'summary_rps': summary_rps
            })
        
        # Рассчитываем агрегированные метрики по всем итерациям
        mean_latency_avg = np.mean([m['latency_avg'] for m in iteration_metrics])
        mean_latency_max = np.mean([m['latency_max'] for m in iteration_metrics])
        mean_rps = np.mean([m['summary_rps'] for m in iteration_metrics])
        stdev_rps = np.std([m['summary_rps'] for m in iteration_metrics])
        
        # Рассчитываем коэффициент вариации RPS (для стабильности)
        cv_rps = (stdev_rps / mean_rps) * 100 if mean_rps > 0 else 0
        
        # Рассчитываем стабильность задержек
        stdev_latency = np.std([m['latency_avg'] for m in iteration_metrics])
        cv_latency = (stdev_latency / mean_latency_avg) * 100 if mean_latency_avg > 0 else 0
        
        data.append({
            'runtime': runtime,
            'timestamp': timestamp,
            'configuration': configuration,
            'iterations': iteration_metrics,
            'mean_latency_avg': mean_latency_avg,
            'mean_latency_max': mean_latency_max, 
            'mean_rps': mean_rps,
            'stdev_rps': stdev_rps,
            'cv_rps': cv_rps,
            'cv_latency': cv_latency,
            'file_path': file_path
        })
    
    return data

def create_rps_bar_chart(data, output_dir='analysis/http'):
    """Создает столбчатую диаграмму среднего RPS по рантаймам"""
    # Проверяем, существует ли директория для выходных файлов
    os.makedirs(output_dir, exist_ok=True)
    
    # Сортируем данные в соответствии с заданным порядком рантаймов
    sorted_data = []
    for runtime in RUNTIME_ORDER:
        for item in data:
            if item['runtime'] == runtime:
                sorted_data.append(item)
    
    # Подготавливаем данные для построения
    runtimes = [RUNTIME_NAMES_RU[item['runtime']] for item in sorted_data]
    mean_rps = [item['mean_rps'] for item in sorted_data]
    stdev_rps = [item['stdev_rps'] for item in sorted_data]
    colors = [RUNTIME_COLORS[item['runtime']] for item in sorted_data]
    
    # Создаем фигуру
    plt.figure(figsize=(10, 6))
    
    # Рисуем столбчатую диаграмму
    bars = plt.bar(runtimes, mean_rps, yerr=stdev_rps, color=colors, 
                  alpha=0.8, capsize=10, edgecolor='gray', linewidth=1)
    
    # Настройка осей и заголовков
    plt.title('Сравнение пропускной способности', fontsize=16, fontweight='bold')
    plt.ylabel('Запросов в секунду (RPS)', fontsize=14)
    plt.ylim(0, max(mean_rps) * 1.2)  # Добавляем немного места для подписей
    plt.grid(axis='y', alpha=0.3)
    
    # Сохраняем график
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '1_http_rps_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_latency_bar_chart(data, output_dir='analysis/http'):
    """Создает групповую диаграмму задержек (средних и максимальных)"""
    # Проверяем, существует ли директория для выходных файлов
    os.makedirs(output_dir, exist_ok=True)
    
    # Сортируем данные в соответствии с заданным порядком рантаймов
    sorted_data = []
    for runtime in RUNTIME_ORDER:
        for item in data:
            if item['runtime'] == runtime:
                sorted_data.append(item)
    
    # Подготавливаем данные для построения
    runtimes = [RUNTIME_NAMES_RU[item['runtime']] for item in sorted_data]
    mean_latency_avg = [item['mean_latency_avg'] for item in sorted_data]
    mean_latency_max = [item['mean_latency_max'] for item in sorted_data]
    colors = [RUNTIME_COLORS[item['runtime']] for item in sorted_data]
    
    # Позиции групп на оси X
    x = np.arange(len(runtimes))
    width = 0.35  # ширина столбца
    
    # Создаем фигуру
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Рисуем группы столбцов
    bars1 = ax.bar(x - width/2, mean_latency_avg, width, label='Средняя задержка', 
                  color=colors, alpha=0.7, edgecolor='gray', linewidth=1)
    bars2 = ax.bar(x + width/2, mean_latency_max, width, label='Максимальная задержка', 
                  color=colors, alpha=0.3, edgecolor='gray', linewidth=1, hatch='////')
    
    # Добавляем значения над столбцами
    for bar, value in zip(bars1, mean_latency_avg):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height * 1.1,
                f'{value:.2f}',
                ha='center', va='bottom', fontsize=10)
    
    for bar, value in zip(bars2, mean_latency_max):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height * 1.1,
                f'{value:.2f}',
                ha='center', va='bottom', fontsize=10)
    
    # Настройка осей и заголовков
    ax.set_title('Сравнение задержек ответа', fontsize=16, fontweight='bold')
    ax.set_ylabel('Задержка (мс)', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(runtimes)
    ax.legend()
    
    # Логарифмическая шкала для оси Y
    ax.set_yscale('log')
    
    # Настраиваем формат чисел на оси Y (без научной нотации)
    ax.yaxis.set_major_formatter(ScalarFormatter())
    
    # Добавляем сетку
    ax.grid(axis='y', alpha=0.3)
    
    # Сохраняем график
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '2_http_latency_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_stability_line_chart(data, output_dir='analysis/http'):
    """Создает линейную диаграмму стабильности производительности по итерациям"""
    # Проверяем, существует ли директория для выходных файлов
    os.makedirs(output_dir, exist_ok=True)
    
    # Создаем фигуру
    plt.figure(figsize=(10, 6))
    
    # Для каждого рантайма рисуем линию RPS по итерациям
    for runtime in RUNTIME_ORDER:
        for item in data:
            if item['runtime'] == runtime:
                # Извлекаем данные по итерациям
                iterations = [i['iteration'] for i in item['iterations']]
                rps_values = [i['summary_rps'] for i in item['iterations']]
                
                # Рисуем линию
                plt.plot(iterations, rps_values, marker='o', linestyle='-', 
                        label=RUNTIME_NAMES_RU[runtime], color=RUNTIME_COLORS[runtime], 
                        linewidth=2, markersize=8)
                
                # Добавляем горизонтальную линию среднего значения
                plt.axhline(y=item['mean_rps'], color=RUNTIME_COLORS[runtime], 
                          linestyle='--', alpha=0.5)
    
    # Настройка осей и заголовков
    plt.title('Стабильность производительности по итерациям', fontsize=16, fontweight='bold')
    plt.xlabel('Итерация', fontsize=14)
    plt.ylabel('Запросов в секунду (RPS)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.xticks(iterations)  # Используем номера итераций как метки на оси X
    plt.legend()
    
    # Сохраняем график
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '3_http_stability_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_radar_chart(data, output_dir='analysis/http'):
    """Создает радарную диаграмму ключевых метрик"""
    # Проверяем, существует ли директория для выходных файлов
    os.makedirs(output_dir, exist_ok=True)
    
    # Подготавливаем данные для нормализации
    metric_data = {
        'mean_rps': [],  # Выше - лучше
        'min_latency': [],  # Ниже - лучше (инвертируем)
        'stability_rps': [],  # Выше - лучше (1 - коэф. вариации)
        'stability_latency': [],  # Выше - лучше (инвертируем)
        'peak_resilience': []  # Выше - лучше (инвертируем макс. задержку)
    }
    
    runtime_data = {}
    
    # Собираем данные по всем рантаймам
    for item in data:
        runtime = item['runtime']
        
        metric_data['mean_rps'].append(item['mean_rps'])
        metric_data['min_latency'].append(item['mean_latency_avg'])
        metric_data['stability_rps'].append(1 - (item['cv_rps'] / 100))  # Преобразуем CV в стабильность
        metric_data['stability_latency'].append(item['cv_latency'])
        metric_data['peak_resilience'].append(item['mean_latency_max'])
        
        runtime_data[runtime] = {
            'mean_rps': item['mean_rps'],
            'min_latency': item['mean_latency_avg'],
            'stability_rps': 1 - (item['cv_rps'] / 100),
            'stability_latency': item['cv_latency'],
            'peak_resilience': item['mean_latency_max']
        }
    
    # Нормализуем данные
    normalized_data = {}
    
    for runtime in runtime_data:
        normalized_data[runtime] = {}
        
        # Метрики, где больше - лучше
        max_rps = max(metric_data['mean_rps'])
        normalized_data[runtime]['mean_rps'] = runtime_data[runtime]['mean_rps'] / max_rps if max_rps > 0 else 0
        
        max_stability_rps = max(metric_data['stability_rps'])
        normalized_data[runtime]['stability_rps'] = runtime_data[runtime]['stability_rps'] / max_stability_rps if max_stability_rps > 0 else 0
        
        # Метрики, где меньше - лучше (инвертируем и нормализуем)
        min_latency = min(metric_data['min_latency'])
        if min_latency > 0 and runtime_data[runtime]['min_latency'] > 0:
            normalized_data[runtime]['min_latency'] = min_latency / runtime_data[runtime]['min_latency']
        else:
            normalized_data[runtime]['min_latency'] = 1.0
        
        min_stability_latency = min(metric_data['stability_latency']) if any(metric_data['stability_latency']) else 1
        if min_stability_latency > 0 and runtime_data[runtime]['stability_latency'] > 0:
            normalized_data[runtime]['stability_latency'] = min_stability_latency / runtime_data[runtime]['stability_latency']
        else:
            normalized_data[runtime]['stability_latency'] = 1.0
        
        min_peak_resilience = min(metric_data['peak_resilience'])
        if min_peak_resilience > 0 and runtime_data[runtime]['peak_resilience'] > 0:
            normalized_data[runtime]['peak_resilience'] = min_peak_resilience / runtime_data[runtime]['peak_resilience']
        else:
            normalized_data[runtime]['peak_resilience'] = 1.0
    
    # Имена категорий для радара
    categories = [
        'Средний RPS', 
        'Минимальная\nсредняя задержка', 
        'Стабильность RPS', 
        'Стабильность\nзадержек', 
        'Устойчивость к\nпиковым нагрузкам'
    ]
    
    # Угол для каждой оси
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Замыкаем круг
    
    # Создаем фигуру
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, polar=True)
    
    # Настройка осей
    plt.xticks(angles[:-1], categories, fontsize=12)
    
    # Настройка направления и метки y-осей
    ax.set_rlabel_position(0)
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=10)
    plt.ylim(0, 1)
    
    # Рисуем радарные линии для каждого рантайма
    for runtime in RUNTIME_ORDER:
        if runtime in normalized_data:
            values = [
                normalized_data[runtime]['mean_rps'],
                normalized_data[runtime]['min_latency'],
                normalized_data[runtime]['stability_rps'],
                normalized_data[runtime]['stability_latency'],
                normalized_data[runtime]['peak_resilience']
            ]
            values += values[:1]  # Замыкаем круг
            
            ax.plot(angles, values, linewidth=2, linestyle='solid', label=RUNTIME_NAMES_RU[runtime], 
                   color=RUNTIME_COLORS[runtime])
            ax.fill(angles, values, color=RUNTIME_COLORS[runtime], alpha=0.25)
    
    # Добавляем заголовок и легенду
    plt.title('Комплексная оценка производительности', fontsize=16, fontweight='bold', y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    # Сохраняем график
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '4_http_radar_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Основная функция для запуска визуализации"""
    # Путь к директории с результатами
    results_dir = 'results/http'
    output_dir = 'analysis/http/results'
    
    # Проверяем, существуют ли директории
    os.makedirs(output_dir, exist_ok=True)
    
    # Загружаем данные бенчмарков
    http_data = load_http_benchmark_data(results_dir)
    
    if not http_data:
        print("Не найдены файлы с результатами HTTP бенчмарков")
        return
    
    # Создаем графики
    create_rps_bar_chart(http_data, output_dir)
    create_latency_bar_chart(http_data, output_dir)
    create_stability_line_chart(http_data, output_dir)
    create_radar_chart(http_data, output_dir)
    
    print(f"Визуализации созданы в директории: {output_dir}")

if __name__ == "__main__":
    main() 