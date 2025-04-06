#!/bin/bash

# Скрипт для последовательного запуска тестов для всех рантаймов
# Использование: ./run_all_benchmarks.sh [iterations]
# [iterations] - количество итераций для каждого рантайма (по умолчанию 3)

ITERATIONS=${1:-3}  # По умолчанию 3 итерации, если не указано иное
RUNTIMES=("node" "deno" "bun")

echo "Запуск бенчмарков для всех рантаймов с $ITERATIONS итерациями каждый"

for runtime in "${RUNTIMES[@]}"; do
    echo "==============================================="
    echo "Запуск бенчмарка для $runtime ($ITERATIONS итераций)..."
    echo "==============================================="
    
    ./benchmark_http.sh "$runtime" "$ITERATIONS"
    
    # Проверка кода возврата
    if [ $? -ne 0 ]; then
        echo "ОШИБКА: Бенчмарк для $runtime завершился с ошибкой!"
    else
        echo "Бенчмарк для $runtime успешно завершен."
    fi
    
    echo ""
    echo "Ожидание 10 секунд перед запуском следующего теста..."
    sleep 10
done

echo "==============================================="
echo "Все тесты завершены! Результаты находятся в директории ./results/"
echo "===============================================" 