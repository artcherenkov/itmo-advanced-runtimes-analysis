/**
 * Бенчмарк алгоритма Фибоначчи для Bun
 */
import { join } from 'node:path';
import { benchmark } from '../utils/metrics.js';
import { preventNumericOptimization, preventInlining } from '../utils/deoptimize.js';

/**
 * Деоптимизированная версия рекурсивной функции Фибоначчи
 * Создаем отдельную версию для корректной работы рекурсии
 */
const fibonacciDeoptimized = (function() {
  /**
   * Рекурсивная реализация вычисления чисел Фибоначчи
   * @param {number} n - Порядковый номер числа в последовательности
   * @returns {number} - n-ное число Фибоначчи
   */
  function fib(n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
  }
  
  // Применяем деоптимизацию
  return preventNumericOptimization(preventInlining(fib));
})();

/**
 * Итеративная реализация вычисления чисел Фибоначчи
 * @param {number} n - Порядковый номер числа в последовательности
 * @returns {number} - n-ное число Фибоначчи
 */
function fibonacciIterative(n) {
  if (n <= 1) return n;
  
  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    const temp = a + b;
    a = b;
    b = temp;
  }
  
  return b;
}

/**
 * Запуск бенчмарка
 */
function runBenchmark() {
  // Получаем входные параметры из аргументов командной строки или переменных окружения
  const args = process.argv.slice(2);
  const n = parseInt(args[0] || process.env.FIB_N) || 40; // Значение n по умолчанию - 40
  const implementation = args[1] || process.env.FIB_IMPL || 'recursive'; // Реализация по умолчанию - рекурсивная
  const iterations = parseInt(args[2] || process.env.ITERATIONS) || 30; // Количество итераций по умолчанию - 30
  
  console.log(`Запуск бенчмарка Фибоначчи для Bun (${Bun.version})`);
  console.log(`- Значение n: ${n}`);
  console.log(`- Реализация: ${implementation}`);
  console.log(`- Количество итераций: ${iterations}`);
  console.log(`- Контейнер: ${process.env.CONTAINER === 'true' ? 'Да' : 'Нет'}`);
  
  // Выбираем функцию для тестирования
  let fnToTest;
  let description;
  
  if (implementation === 'recursive') {
    // Используем предварительно деоптимизированную функцию
    fnToTest = fibonacciDeoptimized;
    description = 'рекурсивная реализация';
  } else {
    fnToTest = preventNumericOptimization(fibonacciIterative);
    description = 'итеративная реализация';
  }
  
  console.log(`Используется ${description} с деоптимизацией`);
  
  // Настраиваем параметры бенчмарка
  const benchmarkOptions = {
    iterations,
    warmupIterations: 3,
    experiment: `fibonacci_${implementation}_n${n}`,
    detailedMetrics: true,
    outputPath: join(import.meta.dir, '../../../results', `bun_fibonacci_${implementation}_n${n}_${Date.now()}.json`)
  };
  
  // Запускаем бенчмарк
  const results = benchmark(fnToTest, [n], benchmarkOptions);
  
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
runBenchmark(); 