#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import glob
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

# Создаем словарь цветов с русскими названиями рантаймов
RUNTIME_COLORS_RU = {RUNTIME_NAMES_RU[runtime]: color for runtime, color in RUNTIME_COLORS.items()}

def load_cold_start_benchmark_data(results_dir='results'):
    """Загружает данные Cold Start бенчмарков из JSON файлов"""
    data = []
    
    # Получаем список всех JSON файлов с Cold Start бенчмарками
    json_files = glob.glob(os.path.join(results_dir, '*cold_start*.json'))
    
    for file_path in json_files:
        with open(file_path, 'r') as f:
            benchmark_data = json.load(f)
            
        # Извлекаем ключевую информацию
        runtime = benchmark_data['runtime']
        version = benchmark_data.get('version', 'Unknown')
        host_system = benchmark_data.get('host_system', {})
        iterations = benchmark_data['iterations']
        
        # Собираем метрики по всем итерациям
        startup_times = [it['startup_time_ms'] for it in iterations]
        first_request_times = [it['first_request_time_ms'] for it in iterations]
        total_times = [it['total_cold_start_time_ms'] for it in iterations]
        
        # Рассчитываем агрегированные метрики
        avg_startup_time = np.mean(startup_times)
        avg_first_request_time = np.mean(first_request_times)
        avg_total_time = np.mean(total_times)
        
        std_startup_time = np.std(startup_times)
        std_first_request_time = np.std(first_request_times)
        std_total_time = np.std(total_times)
        
        # Рассчитываем коэффициент вариации (для стабильности)
        cv_startup = (std_startup_time / avg_startup_time) * 100 if avg_startup_time > 0 else 0
        cv_first_request = (std_first_request_time / avg_first_request_time) * 100 if avg_first_request_time > 0 else 0
        cv_total = (std_total_time / avg_total_time) * 100 if avg_total_time > 0 else 0
        
        # Рассчитываем процентное соотношение фаз
        startup_percentage = (avg_startup_time / avg_total_time) * 100 if avg_total_time > 0 else 0
        first_request_percentage = (avg_first_request_time / avg_total_time) * 100 if avg_total_time > 0 else 0
        
        data.append({
            'runtime': runtime,
            'version': version,
            'host_system': host_system,
            'iterations': iterations,
            'avg_startup_time': avg_startup_time,
            'avg_first_request_time': avg_first_request_time,
            'avg_total_time': avg_total_time,
            'std_startup_time': std_startup_time,
            'std_first_request_time': std_first_request_time,
            'std_total_time': std_total_time,
            'cv_startup': cv_startup,
            'cv_first_request': cv_first_request,
            'cv_total': cv_total,
            'startup_percentage': startup_percentage,
            'first_request_percentage': first_request_percentage,
            'file_path': file_path
        })
    
    return data

def create_combined_iterations_chart(data, output_dir='analysis/cold_start/results'):
    """Создает комбинированную диаграмму всех итераций с разбивкой по фазам"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Для каждого рантайма создаем график
    for runtime in RUNTIME_ORDER:
        runtime_data = None
        for item in data:
            if item['runtime'] == runtime:
                runtime_data = item
                break
        
        if not runtime_data:
            continue
        
        # Извлекаем данные итераций
        iterations = runtime_data['iterations']
        iteration_nums = [it['iteration'] for it in iterations]
        startup_times = [it['startup_time_ms'] for it in iterations]
        first_request_times = [it['first_request_time_ms'] for it in iterations]
        
        # Создаем DataFrame для удобства построения
        df = pd.DataFrame({
            'Итерация': iteration_nums,
            'Время запуска (мс)': startup_times,
            'Время первого запроса (мс)': first_request_times
        })
        
        # Создаем график
        plt.figure(figsize=(14, 8))
        
        # Создаем столбчатую диаграмму с накоплением
        ax = df.plot(
            x='Итерация',
            kind='bar',
            stacked=True,
            color=[RUNTIME_COLORS[runtime], 'lightgray'],
            edgecolor='gray',
            linewidth=1,
            figsize=(14, 8)
        )
        
        # Настройка осей и заголовков
        plt.title(f'Структура холодного старта для {RUNTIME_NAMES_RU[runtime]} по итерациям', fontsize=16, fontweight='bold')
        plt.xlabel('Итерация', fontsize=14)
        plt.ylabel('Время (мс)', fontsize=14)
        plt.grid(axis='y', alpha=0.3)
        plt.legend(['Время запуска (мс)', 'Время первого запроса (мс)'])
        
        # Добавляем подписи с общим временем над столбцами
        for i, (_, row) in enumerate(df.iterrows()):
            total = row['Время запуска (мс)'] + row['Время первого запроса (мс)']
            ax.text(i, total + 5, f'{total:.0f}', ha='center', fontsize=9)
        
        # Сохраняем график
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'1_{runtime}_cold_start_iterations.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    # Создаем общий график для сравнения всех рантаймов
    plt.figure(figsize=(14, 8))
    
    # Подготавливаем данные
    df_comparison = pd.DataFrame(columns=['Runtime', 'Итерация', 'Время запуска (мс)', 'Время первого запроса (мс)', 'Общее время (мс)'])
    
    for item in data:
        runtime = item['runtime']
        iterations = item['iterations']
        
        for it in iterations:
            df_comparison = pd.concat([df_comparison, pd.DataFrame({
                'Runtime': [RUNTIME_NAMES_RU[runtime]],
                'Итерация': [it['iteration']],
                'Время запуска (мс)': [it['startup_time_ms']],
                'Время первого запроса (мс)': [it['first_request_time_ms']],
                'Общее время (мс)': [it['total_cold_start_time_ms']]
            })], ignore_index=True)
    
    # Группируем и вычисляем средние значения
    df_avg = df_comparison.groupby('Runtime').agg({
        'Время запуска (мс)': 'mean',
        'Время первого запроса (мс)': 'mean',
        'Общее время (мс)': 'mean'
    }).reset_index()
    
    # Сортируем DataFrame в соответствии с заданным порядком рантаймов
    runtime_order_ru = [RUNTIME_NAMES_RU[r] for r in RUNTIME_ORDER if r in RUNTIME_NAMES_RU]
    df_avg['Runtime'] = pd.Categorical(df_avg['Runtime'], categories=runtime_order_ru, ordered=True)
    df_avg = df_avg.sort_values('Runtime')
    
    # Создаем столбчатую диаграмму для средних значений
    ax = df_avg.plot(
        x='Runtime',
        y=['Время запуска (мс)', 'Время первого запроса (мс)'],
        kind='bar',
        stacked=True,
        color=[list(RUNTIME_COLORS.values())[i % len(RUNTIME_COLORS)] for i in range(2)],
        edgecolor='gray',
        linewidth=1,
        figsize=(10, 6)
    )
    
    # Настройка графика
    plt.title('Сравнение средних значений холодного старта', fontsize=16, fontweight='bold')
    plt.xlabel('')
    plt.ylabel('Время (мс)', fontsize=14)
    plt.grid(axis='y', alpha=0.3)
    plt.legend(['Время запуска (мс)', 'Время первого запроса (мс)'])
    
    # Добавляем подписи с общим временем над столбцами
    for i, (_, row) in enumerate(df_avg.iterrows()):
        total = row['Время запуска (мс)'] + row['Время первого запроса (мс)']
        ax.text(i, total + 5, f'{total:.0f}', ha='center', fontsize=10)
    
    # Сохраняем график
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '1_combined_cold_start_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_boxplot_chart(data, output_dir='analysis/cold_start/results'):
    """Создает диаграмму "ящик с усами" для всех метрик холодного старта"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Подготавливаем данные
    boxplot_data = []
    
    for item in data:
        runtime = item['runtime']
        iterations = item['iterations']
        
        for it in iterations:
            boxplot_data.append({
                'Runtime': RUNTIME_NAMES_RU[runtime],
                'Метрика': 'Время запуска',
                'Значение (мс)': it['startup_time_ms']
            })
            boxplot_data.append({
                'Runtime': RUNTIME_NAMES_RU[runtime],
                'Метрика': 'Время первого запроса',
                'Значение (мс)': it['first_request_time_ms']
            })
            boxplot_data.append({
                'Runtime': RUNTIME_NAMES_RU[runtime],
                'Метрика': 'Общее время холодного старта',
                'Значение (мс)': it['total_cold_start_time_ms']
            })
    
    # Создаем DataFrame
    df_boxplot = pd.DataFrame(boxplot_data)
    
    # Сортируем DataFrame в соответствии с заданным порядком рантаймов
    runtime_order_ru = [RUNTIME_NAMES_RU[r] for r in RUNTIME_ORDER if r in RUNTIME_NAMES_RU]
    df_boxplot['Runtime'] = pd.Categorical(df_boxplot['Runtime'], categories=runtime_order_ru, ordered=True)
    df_boxplot = df_boxplot.sort_values(['Runtime', 'Метрика'])
    
    # Создаем ящик с усами
    plt.figure(figsize=(14, 8))
    
    # Используем seaborn для создания красивого ящика с усами
    ax = sns.boxplot(
        x='Метрика',
        y='Значение (мс)',
        hue='Runtime',
        data=df_boxplot,
        palette=RUNTIME_COLORS_RU,  # Используем словарь с русскими названиями
        width=0.6,
        fliersize=3
    )
    
    # Настройка графика
    plt.title('Статистическое распределение метрик холодного старта', fontsize=16, fontweight='bold')
    plt.xlabel('')
    plt.ylabel('Время (мс)', fontsize=14)
    plt.grid(axis='y', alpha=0.3)
    plt.legend(title='')
    
    # Сохраняем график
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '2_boxplot_cold_start_metrics.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_phases_pie_chart(data, output_dir='analysis/cold_start/results'):
    """Создает круговую диаграмму соотношения фаз холодного старта для каждого рантайма"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Создаем подграфики для каждого рантайма
    fig, axes = plt.subplots(1, len(data), figsize=(15, 5))
    
    # Если только один рантайм, преобразуем в список
    if len(data) == 1:
        axes = [axes]
    
    # Сортируем данные в соответствии с заданным порядком рантаймов
    sorted_data = []
    for runtime in RUNTIME_ORDER:
        for item in data:
            if item['runtime'] == runtime:
                sorted_data.append(item)
    
    # Для каждого рантайма создаем круговую диаграмму
    for i, item in enumerate(sorted_data):
        runtime = item['runtime']
        startup_percentage = item['startup_percentage']
        first_request_percentage = item['first_request_percentage']
        
        # Данные для круговой диаграммы
        sizes = [startup_percentage, first_request_percentage]
        labels = ['Время запуска', 'Время первого запроса']
        colors = [RUNTIME_COLORS[runtime], 'lightgray']
        
        # Создаем круговую диаграмму
        axes[i].pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'edgecolor': 'w', 'linewidth': 1}
        )
        axes[i].set_title(f'{RUNTIME_NAMES_RU[runtime]}', fontsize=14)
        axes[i].axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    
    # Общий заголовок
    plt.suptitle('Соотношение фаз холодного старта', fontsize=16, fontweight='bold')
    
    # Сохраняем график
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '3_pie_chart_phases.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_stability_plot(data, output_dir='analysis/cold_start/results'):
    """Создает график стабильности холодного старта по итерациям"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Создаем фигуру
    plt.figure(figsize=(14, 8))
    
    # Обрабатываем рантаймы в заданном порядке
    for runtime in RUNTIME_ORDER:
        runtime_data = None
        for item in data:
            if item['runtime'] == runtime:
                runtime_data = item
                break
        
        if not runtime_data:
            continue
        
        iterations = runtime_data['iterations']
        iteration_nums = [it['iteration'] for it in iterations]
        total_cold_start_times = [it['total_cold_start_time_ms'] for it in iterations]
        
        # Рисуем линию для текущего рантайма
        plt.plot(
            iteration_nums, 
            total_cold_start_times, 
            marker='o', 
            linestyle='-', 
            label=RUNTIME_NAMES_RU[runtime], 
            color=RUNTIME_COLORS[runtime], 
            linewidth=2,
            markersize=6
        )
        
        # Добавляем медиану как горизонтальную линию
        median_time = np.median(total_cold_start_times)
        plt.axhline(
            y=median_time, 
            color=RUNTIME_COLORS[runtime], 
            linestyle='--', 
            alpha=0.6,
            linewidth=1
        )
        
        # Добавляем p25 и p75 как прозрачную область
        p25 = np.percentile(total_cold_start_times, 25)
        p75 = np.percentile(total_cold_start_times, 75)
        plt.fill_between(
            iteration_nums,
            [p25] * len(iteration_nums),
            [p75] * len(iteration_nums),
            color=RUNTIME_COLORS[runtime],
            alpha=0.1
        )
    
    # Настройка осей и заголовков
    plt.title('Стабильность времени холодного старта по итерациям', fontsize=16, fontweight='bold')
    plt.xlabel('Итерация', fontsize=14)
    plt.ylabel('Общее время холодного старта (мс)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(title='Рантайм', fontsize=12)
    
    # Сохраняем график
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '4_cold_start_stability.png'), dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Основная функция для запуска визуализации"""
    # Путь к директории с результатами
    results_dir = 'results'
    output_dir = 'analysis/cold_start/results'
    
    # Проверяем, существуют ли директории
    os.makedirs(output_dir, exist_ok=True)
    
    # Загружаем данные бенчмарков
    cold_start_data = load_cold_start_benchmark_data(results_dir)
    
    if not cold_start_data:
        print("Не найдены файлы с результатами Cold Start бенчмарков")
        return
    
    # Создаем графики
    create_combined_iterations_chart(cold_start_data, output_dir)
    create_boxplot_chart(cold_start_data, output_dir)
    create_phases_pie_chart(cold_start_data, output_dir)
    create_stability_plot(cold_start_data, output_dir)
    
    print(f"Визуализации созданы в директории: {output_dir}")

if __name__ == "__main__":
    main() 