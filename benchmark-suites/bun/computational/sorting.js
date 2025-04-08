/**
 * Бенчмарк алгоритмов сортировки для Bun
 */
import path from 'path';
import { fileURLToPath } from 'url';
import { benchmark } from './utils/metrics.mjs';
import { preventNumericOptimization, preventInlining } from './utils/deoptimize.mjs';

// Получаем текущую директорию через ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

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
const quickSortDeoptimized = preventNumericOptimization(preventInlining(quickSort));

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
const insertionSortDeoptimized = preventNumericOptimization(preventInlining(insertionSort));

/**
 * Запуск бенчмарка
 */
async function runBenchmark() {
  // Получаем входные параметры из аргументов командной строки или переменных окружения
  const size = parseInt(process.env.ARRAY_SIZE) || 10000;
  const algorithm = process.env.SORT_ALGORITHM || 'quicksort';
  const iterations = parseInt(process.env.ITERATIONS) || 30;
  
  // Выводим информацию о запуске бенчмарка
  console.log(`Запуск бенчмарка сортировки для Bun (${Bun.version})`);
  console.log(`- Размер массива: ${size} элементов`);
  console.log(`- Алгоритм: ${algorithm}`);
  console.log(`- Количество итераций: ${iterations}`);
  console.log(`- Контейнер: ${process.env.CONTAINER === 'true' ? 'Да' : 'Нет'}`);
  
  // Генерируем тестовый массив
  const testArray = generateRandomArray(size);
  
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
  
  // Проверка наличия возможности принудительной сборки мусора
  if (global.gc) {
    console.log('Принудительная сборка мусора включена (--expose-gc)');
  } else {
    console.log('Принудительная сборка мусора недоступна. Для включения запустите с флагом --expose-gc');
  }
  
  // Настраиваем параметры бенчмарка
  const benchmarkOptions = {
    iterations,
    warmupIterations: 3,
    experiment: `sorting_${algorithm}_size${size}`,
    detailedMetrics: true,
    outputPath: path.join(__dirname, '../../../results/computational', `bun_sorting_${algorithm}_size${size}_${Date.now()}.json`)
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
  process.exit(1);
}); 