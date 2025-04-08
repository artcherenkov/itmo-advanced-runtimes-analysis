/**
 * Утилиты для сбора метрик в Deno
 */
import { formatMetrics, saveResults } from '../../../metrics-interface.mjs';

/**
 * Получает текущее использование CPU
 * @returns {Object} Объект с информацией об использовании CPU
 */
export function getCpuUsage() {
  // В Deno получение CPU usage отличается от Node.js
  // Используем упрощенный вариант
  return {
    cpuCores: navigator.hardwareConcurrency || 1,
    user: 0,
    system: 0,
    idle: 0,
    timestamp: Date.now()
  };
}

/**
 * Получает текущее использование памяти
 * @returns {Object} Объект с информацией об использовании памяти
 */
export function getMemoryUsage() {
  // В Deno используем Deno.memoryUsage() вместо process.memoryUsage()
  const memoryInfo = Deno.memoryUsage();
  return {
    ...memoryInfo,
    totalMemory: "not available", // В Deno нет прямого эквивалента os.totalmem()
    freeMemory: "not available",  // В Deno нет прямого эквивалента os.freemem()
    timestamp: Date.now()
  };
}

/**
 * Стабилизирует систему перед измерениями
 * @returns {void}
 */
export function stabilizeSystem() {
  // В Deno нет прямого эквивалента global.gc(),
  // но мы все равно делаем паузу для стабилизации системы
  const startTime = Date.now();
  while (Date.now() - startTime < 20) {
    // Spin wait
  }
}

/**
 * Проводит бенчмарк функции и собирает метрики
 * @param {Function} fn - Функция для тестирования
 * @param {Array} args - Аргументы функции
 * @param {Object} options - Параметры бенчмарка
 * @returns {Object} - Результаты бенчмарка
 */
export async function benchmark(fn, args, options = {}) {
  const {
    iterations = 30,
    warmupIterations = 5,
    experiment = 'unknown',
    outputPath,
    detailedMetrics = true,
  } = options;
  
  // Запускаем прогрев для стабилизации
  console.log(`Разогрев (${warmupIterations} итераций)...`);
  for (let i = 0; i < warmupIterations; i++) {
    fn(...args);
  }
  
  // Начинаем замеры
  console.log(`Запуск бенчмарка (${iterations} итераций)...`);
  
  // Собираем начальные метрики
  const cpuBefore = getCpuUsage();
  const memoryBefore = getMemoryUsage();
  
  // Массив для хранения времени выполнения
  const executionTimes = [];
  
  // Массив для хранения детальных метрик по каждой итерации
  const detailedIterationMetrics = [];
  
  // Запускаем тест
  for (let i = 0; i < iterations; i++) {
    // Стабилизируем систему перед каждым измерением
    stabilizeSystem();
    
    // Замеряем память до выполнения
    const memoryBeforeIteration = detailedMetrics ? getMemoryUsage() : null;
    
    // Засекаем время выполнения
    const startTime = performance.now() * 1_000_000; // переводим в наносекунды
    fn(...args);
    const endTime = performance.now() * 1_000_000;
    
    // Замеряем память после выполнения
    const memoryAfterIteration = detailedMetrics ? getMemoryUsage() : null;
    
    // Вычисляем время выполнения в наносекундах
    const executionTime = endTime - startTime;
    executionTimes.push(executionTime);
    
    // Сохраняем детальные метрики для этой итерации
    if (detailedMetrics) {
      detailedIterationMetrics.push({
        iteration: i + 1,
        executionTime,
        memory: {
          before: memoryBeforeIteration,
          after: memoryAfterIteration,
          diff: {
            rss: memoryAfterIteration.rss - memoryBeforeIteration.rss,
            heapTotal: (memoryAfterIteration.heapTotal || 0) - (memoryBeforeIteration.heapTotal || 0),
            heapUsed: (memoryAfterIteration.heapUsed || 0) - (memoryBeforeIteration.heapUsed || 0),
            external: (memoryAfterIteration.external || 0) - (memoryBeforeIteration.external || 0)
          }
        }
      });
    }
    
    // Отображаем прогресс
    if (i % 5 === 0 || i === iterations - 1) {
      console.log(`Прогресс: ${Math.round(((i + 1) / iterations) * 100)}%`);
    }
  }
  
  // Собираем конечные метрики
  const cpuAfter = getCpuUsage();
  const memoryAfter = getMemoryUsage();
  
  // Готовим объект метрик
  const metrics = formatMetrics(
    'deno',
    Deno.version.deno,
    experiment,
    executionTimes,
    { before: memoryBefore, after: memoryAfter },
    { before: cpuBefore, after: cpuAfter, cpuCores: cpuBefore.cpuCores }
  );
  
  // Добавляем детальные метрики по итерациям
  if (detailedMetrics) {
    metrics.detailedIterationMetrics = detailedIterationMetrics;
  }
  
  // Сохраняем результаты, если указан путь
  if (outputPath) {
    await saveResults(metrics, outputPath);
  }
  
  return metrics;
} 