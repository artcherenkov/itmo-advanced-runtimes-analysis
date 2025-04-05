/**
 * Утилиты для сбора метрик в Deno
 */
import { join, dirname } from 'https://deno.land/std/path/mod.ts';
import { formatMetrics } from '../../metrics-interface.mjs';

/**
 * Получает текущее использование CPU
 * @returns {Object} Объект с информацией об использовании CPU
 */
function getCpuUsage() {
  const cpuCores = navigator.hardwareConcurrency;
  
  return {
    cpuCores,
    user: performance.now(), // Deno не предоставляет прямого доступа к использованию CPU
    system: 0,
    idle: 0,
    timestamp: Date.now()
  };
}

/**
 * Получает текущее использование памяти
 * @returns {Object} Объект с информацией об использовании памяти
 */
function getMemoryUsage() {
  // Используем Deno.memoryUsage() для получения информации о памяти
  const memoryInfo = Deno.memoryUsage();
  
  return {
    ...memoryInfo,
    // Добавляем совместимые поля для сравнения с Node.js
    rss: memoryInfo.rss,
    heapTotal: memoryInfo.heapTotal,
    heapUsed: memoryInfo.heapUsed,
    external: memoryInfo.external || 0,
    totalMemory: 'unknown', // Deno не предоставляет полный объем памяти
    freeMemory: 'unknown',
    timestamp: Date.now()
  };
}

/**
 * Стабилизирует систему перед измерениями
 * @returns {void}
 */
function stabilizeSystem() {
  // Создаем давление на сборщик мусора
  const garbage = [];
  for (let i = 0; i < 100; i++) {
    garbage.push(new Array(1000).fill(0));
  }
  
  // Небольшая пауза для стабилизации системы
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
function benchmark(fn, args, options = {}) {
  const {
    iterations = 30,
    warmupIterations = 5,
    experiment = 'unknown',
    outputPath = join(Deno.cwd(), '../../results', `deno_${experiment}_${Date.now()}.json`),
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
    
    // Используем performance.now() для замера времени с преобразованием в наносекунды
    const startTime = performance.now();
    fn(...args);
    const endTime = performance.now();
    
    // Замеряем память после выполнения
    const memoryAfterIteration = detailedMetrics ? getMemoryUsage() : null;
    
    // Вычисляем время выполнения в наносекундах
    const executionTime = (endTime - startTime) * 1_000_000; // миллисекунды в наносекунды
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
            heapTotal: memoryAfterIteration.heapTotal - memoryBeforeIteration.heapTotal,
            heapUsed: memoryAfterIteration.heapUsed - memoryBeforeIteration.heapUsed,
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
  
  // Получаем версию Deno
  const denoVersion = Deno.version.deno;
  
  // Готовим объект метрик
  const metrics = formatMetrics(
    'deno',
    denoVersion,
    experiment,
    executionTimes,
    { before: memoryBefore, after: memoryAfter },
    { before: cpuBefore, after: cpuAfter, cpuCores: cpuBefore.cpuCores }
  );
  
  // Добавляем детальные метрики по итерациям
  if (detailedMetrics) {
    metrics.detailedIterationMetrics = detailedIterationMetrics;
  }
  
  // Используем встроенный метод metrics-interface для сохранения результатов
  try {
    Deno.writeTextFileSync(outputPath, JSON.stringify(metrics, null, 2));
    console.log(`Результаты сохранены в ${outputPath}`);
  } catch (error) {
    console.error(`Ошибка при сохранении результатов: ${error.message}`);
    
    // Пробуем создать директорию вручную
    try {
      Deno.mkdirSync(dirname(outputPath), { recursive: true });
      Deno.writeTextFileSync(outputPath, JSON.stringify(metrics, null, 2));
      console.log(`Результаты сохранены в ${outputPath} после создания директории`);
    } catch (e) {
      console.error(`Не удалось сохранить результаты даже после создания директории: ${e.message}`);
    }
  }
  
  return metrics;
}

export {
  benchmark,
  getCpuUsage,
  getMemoryUsage
}; 