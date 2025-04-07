#!/bin/bash

# Скрипт для запуска всех анализаторов и создания графиков

echo "Запуск анализаторов..."

# Запуск анализатора HTTP-бенчмарков
echo "Анализ HTTP-бенчмарков..."
python3 analysis/analyze_http_benchmarks.py

# Запуск анализатора асинхронных бенчмарков
echo "Анализ асинхронных бенчмарков..."
python3 analysis/analyze_async_benchmarks.py

echo "Все анализаторы выполнены. Графики сохранены в директории ./results/charts/" 