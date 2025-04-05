/**
 * Утилиты для сбора метрик в Bun
 */
import { writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import os from 'node:os';

import { formatMetrics } from '../../metrics-interface.mjs';

/**
 * Получает текущее использование CPU
 * @returns {Object} Объект с информацией об использовании CPU
 */
function getCpuUsage() {
  const cpus = os.cpus();
  const cpuCores = cpus.length;
  
  // Получаем общее время CPU для всех ядер
  const totalCpuTime = cpus.reduce((acc, cpu) => {
    return {
      user: acc.user + cpu.times.user,
      nice: acc.nice + cpu.times.nice,
      sys: acc.sys + cpu.times.sys,
      idle: acc.idle + cpu.times.idle,
      irq: acc.irq + cpu.times.irq,
    };
  }, { user: 0, nice: 0, sys: 0, idle: 0, irq: 0 });
  
  return {
    cpuCores,
    user: totalCpuTime.user,
    system: totalCpuTime.sys,
    idle: totalCpuTime.idle,
    timestamp: Date.now()
  };
}

/**
 * Получает текущее использование памяти
 * @returns {Object} Объект с информацией об использовании памяти
 */
function getMemoryUsage() {
  // Bun имеет встроенный API для получения информации о памяти
  const memoryInfo = process.memoryUsage();
  
  return {
    ...memoryInfo,
    totalMemory: `${Math.round(os.totalmem() / (1024 * 1024))}MB`,
    freeMemory: `${Math.round(os.freemem() / (1024 * 1024))}MB`,
    timestamp: Date.now()
  };
}

/**
 * Стабилизирует систему перед измерениями
 * @returns {void}
 */
function stabilizeSystem() {
  // В Bun пока нет прямого доступа к сборщику мусора
  // Но можем создать давление на GC
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
    outputPath = join(import.meta.dir, '../../../results', `bun_${experiment}_${Date.now()}.json`),
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
    
    // Используем Bun.nanoseconds() для высокоточного замера времени
    const startTime = Bun.nanoseconds();
    fn(...args);
    const endTime = Bun.nanoseconds();
    
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
            heapTotal: memoryAfterIteration.heapTotal - memoryBeforeIteration.heapTotal,
            heapUsed: memoryAfterIteration.heapUsed - memoryBeforeIteration.heapUsed,
            external: memoryAfterIteration.external - memoryBeforeIteration.external
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
  
  // Получаем версию Bun
  const bunVersion = Bun.version;
  
  // Готовим объект метрик
  const metrics = formatMetrics(
    'bun',
    bunVersion,
    experiment,
    executionTimes,
    { before: memoryBefore, after: memoryAfter },
    { before: cpuBefore, after: cpuAfter, cpuCores: cpuBefore.cpuCores }
  );
  
  // Добавляем детальные метрики по итерациям
  if (detailedMetrics) {
    metrics.detailedIterationMetrics = detailedIterationMetrics;
  }
  
  // Сохраняем результаты
  try {
    const dir = dirname(outputPath);
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
    writeFileSync(outputPath, JSON.stringify(metrics, null, 2));
    console.log(`Результаты сохранены в ${outputPath}`);
  } catch (error) {
    console.error(`Ошибка при сохранении результатов: ${error.message}`);
  }
  
  return metrics;
}

export {
  benchmark,
  getCpuUsage,
  getMemoryUsage
}; 