/**
 * Бенчмарк умножения матриц для Bun
 */
import path from 'path';
import { fileURLToPath } from 'url';
import { benchmark } from './utils/metrics.mjs';
import { preventNumericOptimization, preventInlining } from './utils/deoptimize.mjs';

// Получаем текущую директорию через ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Создает матрицу заданного размера со случайными значениями
 * @param {number} rows - Количество строк
 * @param {number} cols - Количество столбцов
 * @returns {Array<Array<number>>} - Матрица со случайными значениями
 */
function createRandomMatrix(rows, cols) {
  return Array.from({ length: rows }, () => 
    Array.from({ length: cols }, () => Math.floor(Math.random() * 10))
  );
}

/**
 * Наивное умножение матриц
 * @param {Array<Array<number>>} a - Первая матрица
 * @param {Array<Array<number>>} b - Вторая матрица
 * @returns {Array<Array<number>>} - Результат умножения матриц
 */
function naiveMatrixMultiply(a, b) {
  const rowsA = a.length;
  const colsA = a[0].length;
  const colsB = b[0].length;
  
  // Проверяем, что матрицы совместимы для умножения
  if (colsA !== b.length) {
    throw new Error('Размерности матриц несовместимы для умножения');
  }
  
  // Создаем матрицу-результат
  const result = Array.from({ length: rowsA }, () => 
    Array.from({ length: colsB }, () => 0)
  );
  
  // Выполняем умножение
  for (let i = 0; i < rowsA; i++) {
    for (let j = 0; j < colsB; j++) {
      for (let k = 0; k < colsA; k++) {
        result[i][j] += a[i][k] * b[k][j];
      }
    }
  }
  
  return result;
}

/**
 * Умножение матриц с использованием оптимизированного порядка циклов
 * @param {Array<Array<number>>} a - Первая матрица
 * @param {Array<Array<number>>} b - Вторая матрица
 * @returns {Array<Array<number>>} - Результат умножения матриц
 */
function optimizedMatrixMultiply(a, b) {
  const rowsA = a.length;
  const colsA = a[0].length;
  const colsB = b[0].length;
  
  // Проверяем, что матрицы совместимы для умножения
  if (colsA !== b.length) {
    throw new Error('Размерности матриц несовместимы для умножения');
  }
  
  // Создаем матрицу-результат
  const result = Array.from({ length: rowsA }, () => 
    Array.from({ length: colsB }, () => 0)
  );
  
  // Выполняем умножение с оптимизированным порядком циклов
  for (let i = 0; i < rowsA; i++) {
    for (let k = 0; k < colsA; k++) {
      for (let j = 0; j < colsB; j++) {
        result[i][j] += a[i][k] * b[k][j];
      }
    }
  }
  
  return result;
}

// Деоптимизированные версии функций
const naiveMatrixMultiplyDeoptimized = preventNumericOptimization(naiveMatrixMultiply);
const optimizedMatrixMultiplyDeoptimized = preventNumericOptimization(optimizedMatrixMultiply);

/**
 * Запуск бенчмарка
 */
async function runBenchmark() {
  // Получаем входные параметры из аргументов командной строки или переменных окружения
  const matrixSize = parseInt(process.env.MATRIX_SIZE) || 250;
  const algorithm = process.env.MATRIX_ALGORITHM || 'naive';
  const iterations = parseInt(process.env.ITERATIONS) || 30;
  
  console.log(`Запуск бенчмарка умножения матриц для Bun (${Bun.version})`);
  console.log(`- Размер матрицы: ${matrixSize}x${matrixSize}`);
  console.log(`- Алгоритм: ${algorithm}`);
  console.log(`- Количество итераций: ${iterations}`);
  console.log(`- Контейнер: ${process.env.CONTAINER === 'true' ? 'Да' : 'Нет'}`);
  
  // Создаем тестовые матрицы
  const matrixA = createRandomMatrix(matrixSize, matrixSize);
  const matrixB = createRandomMatrix(matrixSize, matrixSize);
  
  // Выбираем функцию для тестирования
  let fnToTest;
  let description;
  
  if (algorithm === 'naive') {
    fnToTest = naiveMatrixMultiplyDeoptimized;
    description = 'наивный алгоритм';
  } else {
    fnToTest = optimizedMatrixMultiplyDeoptimized;
    description = 'оптимизированный алгоритм';
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
    experiment: `matrix_${algorithm}_size${matrixSize}`,
    detailedMetrics: true,
    outputPath: path.join(__dirname, '../../../results/computational', `bun_matrix_${algorithm}_size${matrixSize}_${Date.now()}.json`)
  };
  
  // Запускаем бенчмарк
  const results = await benchmark(fnToTest, [matrixA, matrixB], benchmarkOptions);
  
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