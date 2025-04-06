/**
 * Бенчмарк алгоритма сортировки для Deno
 */
import { join } from "https://deno.land/std/path/mod.ts";
import { benchmark } from '../utils/metrics.js';
import { preventOptimization, preventNumericOptimization } from '../utils/deoptimize.js';

/**
 * Создает массив случайных чисел заданного размера
 * @param {number} size - Размер массива
 * @returns {Array<number>} - Массив случайных чисел
 */
function generateRandomArray(size) {
  return Array.from({ length: size }, () => Math.floor(Math.random() * 10000));
}

/**
 * Реализация QuickSort
 * @param {Array<number>} arr - Массив для сортировки
 * @returns {Array<number>} - Отсортированный массив
 */
function quickSort(arr) {
  if (arr.length <= 1) return arr;
  
  const pivot = arr[Math.floor(arr.length / 2)];
  const left = arr.filter(x => x < pivot);
  const middle = arr.filter(x => x === pivot);
  const right = arr.filter(x => x > pivot);
  
  return [...quickSort(left), ...middle, ...quickSort(right)];
}

/**
 * Деоптимизированная версия QuickSort
 */
const quickSortDeoptimized = preventNumericOptimization(preventOptimization(quickSort));

/**
 * Реализация сортировки вставками
 * @param {Array<number>} arr - Массив для сортировки
 * @returns {Array<number>} - Отсортированный массив
 */
function insertionSort(arr) {
  const result = [...arr];
  
  for (let i = 1; i < result.length; i++) {
    const current = result[i];
    let j = i - 1;
    
    while (j >= 0 && result[j] > current) {
      result[j + 1] = result[j];
      j--;
    }
    
    result[j + 1] = current;
  }
  
  return result;
}

/**
 * Деоптимизированная версия сортировки вставками
 */
const insertionSortDeoptimized = preventNumericOptimization(preventOptimization(insertionSort));

/**
 * Запуск бенчмарка
 */
async function runBenchmark() {
  // Получаем входные параметры из аргументов командной строки или переменных окружения
  const arraySize = parseInt(Deno.env.get("ARRAY_SIZE")) || 10000;
  const algorithm = Deno.env.get("SORT_ALGORITHM") || 'quicksort';
  const iterations = parseInt(Deno.env.get("ITERATIONS")) || 30;
  
  console.log(`Запуск бенчмарка сортировки для Deno (${Deno.version.deno})`);
  console.log(`- Размер массива: ${arraySize}`);
  console.log(`- Алгоритм: ${algorithm}`);
  console.log(`- Количество итераций: ${iterations}`);
  console.log(`- Контейнер: ${Deno.env.get("CONTAINER") === 'true' ? 'Да' : 'Нет'}`);
  
  // Генерируем тестовый массив
  const testArray = generateRandomArray(arraySize);
  
  // Выбираем функцию для тестирования
  let fnToTest;
  let description;
  
  if (algorithm === 'quicksort') {
    fnToTest = quickSortDeoptimized;
    description = 'QuickSort';
  } else {
    fnToTest = insertionSortDeoptimized;
    description = 'Сортировка вставками';
  }
  
  console.log(`Используется ${description} с деоптимизацией`);
  
  // Настраиваем параметры бенчмарка
  const benchmarkOptions = {
    iterations,
    warmupIterations: 3,
    experiment: `sorting_${algorithm}_size${arraySize}`,
    detailedMetrics: true,
    outputPath: '/app/results/' + `deno_sorting_${algorithm}_size${arraySize}_${Date.now()}.json`
  };
  
  // Запускаем бенчмарк
  const results = await benchmark(fnToTest, [testArray], benchmarkOptions);
  
  console.log('\nБенчмарк завершен!');
  console.log(`Среднее время выполнения: ${(results.statistics.mean / 1_000_000).toFixed(3)} мс`);
  console.log(`Медиана времени выполнения: ${(results.statistics.median / 1_000_000).toFixed(3)} мс`);
  console.log(`Стандартное отклонение: ${(results.statistics.stdDev / 1_000_000).toFixed(3)} мс`);
  console.log(`95-й процентиль: ${(results.statistics.p95 / 1_000_000).toFixed(3)} мс`);
  
  // Выводим информацию о потреблении памяти
  const memoryDiff = results.metrics.memoryUsage.diff;
  console.log('\nИзменение использования памяти:');
  console.log(`RSS: ${(memoryDiff.rss / (1024 * 1024)).toFixed(2)} МБ`);
  console.log(`Heap Total: ${(memoryDiff.heapTotal / (1024 * 1024)).toFixed(2)} МБ`);
  console.log(`Heap Used: ${(memoryDiff.heapUsed / (1024 * 1024)).toFixed(2)} МБ`);
  
  console.log(`\nРезультаты сохранены в: ${benchmarkOptions.outputPath}`);
  
  return results;
}

// Запускаем бенчмарк
runBenchmark().catch(err => {
  console.error("Ошибка при выполнении бенчмарка:", err);
  Deno.exit(1);
}); 