#!/bin/bash

# Проверяем наличие необходимых пакетов Python
echo "Проверка необходимых пакетов..."
pip install numpy pandas matplotlib seaborn plotly scipy kaleido

# Запускаем скрипт анализа
echo "Запуск анализа бенчмарков..."
python analysis/computational/benchmark_visualization.py

echo "Анализ завершен!"
echo "Результаты доступны в директории: analysis/computational/results" 