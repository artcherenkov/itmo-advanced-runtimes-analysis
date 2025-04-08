/**
 * Бенчмарк алгоритма Фибоначчи для Deno
 */
import * as path from 'https://deno.land/std/path/mod.ts';
import { benchmark } from './utils/metrics.mjs';
import { preventNumericOptimization, preventInlining } from './utils/deoptimize.mjs';

// В Deno не требуется fileURLToPath, используем прямой путь
const __dirname = new URL('.', import.meta.url).pathname;

/**
 * Рекурсивная реализация вычисления чисел Фибоначчи
 * @param {number} n - Порядковый номер числа в последовательности
 * @returns {number} - n-ное число Фибоначчи
 */
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

/**
 * Деоптимизированная версия рекурсивной функции Фибоначчи
 */
const fibonacciDeoptimized = (function() {
  // Создаем замыкание для сохранения рекурсивной ссылки
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
async function runBenchmark() {
  // Получаем входные параметры из аргументов командной строки или переменных окружения
  const n = parseInt(Deno.env.get("FIB_N")) || 40; // Значение n по умолчанию - 40
  const implementation = Deno.env.get("FIB_IMPL") || 'recursive'; // Реализация по умолчанию - рекурсивная
  const iterations = parseInt(Deno.env.get("ITERATIONS")) || 30; // Количество итераций по умолчанию - 30
  
  console.log(`Запуск бенчмарка Фибоначчи для Deno (${Deno.version.deno})`);
  console.log(`- Значение n: ${n}`);
  console.log(`- Реализация: ${implementation}`);
  console.log(`- Количество итераций: ${iterations}`);
  console.log(`- Контейнер: ${Deno.env.get("CONTAINER") === 'true' ? 'Да' : 'Нет'}`);
  
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

  // В Deno нет принудительной сборки мусора как в Node.js
  console.log('Принудительная сборка мусора недоступна в Deno');
  
  // Настраиваем параметры бенчмарка
  const benchmarkOptions = {
    iterations,
    warmupIterations: 3,
    experiment: `fibonacci_${implementation}_n${n}`,
    detailedMetrics: true,
    outputPath: path.join(__dirname, '../../../results/computational', `deno_fibonacci_${implementation}_n${n}_${Date.now()}.json`)
  };
  
  // Запускаем бенчмарк
  const results = await benchmark(fnToTest, [n], benchmarkOptions);
  
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