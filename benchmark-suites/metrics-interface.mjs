/**
 * Стандартный интерфейс метрик для всех рантаймов - ESM версия
 */

/**
 * Формирует стандартизированный объект результатов
 * @param {string} runtime - Идентификатор рантайма (node, deno, bun)
 * @param {string} version - Версия рантайма
 * @param {string} experiment - Название эксперимента
 * @param {Array<number>} executionTimes - Массив времен выполнения (наносекунды)
 * @param {Object} memoryUsage - Использование памяти до и после теста
 * @param {Object} cpuUsage - Использование CPU до и после теста
 * @returns {Object} - Стандартизированный объект результатов
 */
export function formatMetrics(runtime, version, experiment, executionTimes, memoryUsage, cpuUsage) {
  // Вычисление статистики
  const mean = executionTimes.reduce((a, b) => a + b, 0) / executionTimes.length;
  const sorted = [...executionTimes].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const stdDev = Math.sqrt(
    executionTimes.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / executionTimes.length
  );
  const p95 = sorted[Math.floor(sorted.length * 0.95)];
  const p99 = sorted[Math.floor(sorted.length * 0.99)];
  
  // Определение platformOS для поддержки различных рантаймов
  let platformOS = 'unknown';
  let isContainer = false;
  
  // Проверка доступности process для разных рантаймов
  if (typeof process !== 'undefined') {
    platformOS = process.platform;
    isContainer = process.env.CONTAINER === 'true';
  } else if (typeof Deno !== 'undefined') {
    platformOS = Deno.build.os;
    isContainer = Deno.env.get('CONTAINER') === 'true';
  } else if (typeof Bun !== 'undefined') {
    platformOS = process.platform;
    isContainer = process.env.CONTAINER === 'true';
  }
  
  return {
    runtime,
    version,
    experiment,
    timestamp: new Date().toISOString(),
    environment: {
      os: platformOS,
      container: isContainer,
      cpuCores: cpuUsage.cpuCores || 'unknown',
      memory: memoryUsage.before.totalMemory || 'unknown'
    },
    metrics: {
      executionTimes,
      averageExecutionTime: mean,
      memoryUsage: {
        before: memoryUsage.before,
        after: memoryUsage.after,
        diff: {
          rss: memoryUsage.after.rss - memoryUsage.before.rss,
          heapTotal: memoryUsage.after.heapTotal - memoryUsage.before.heapTotal,
          heapUsed: memoryUsage.after.heapUsed - memoryUsage.before.heapUsed,
          external: memoryUsage.after.external - memoryUsage.before.external
        }
      },
      cpuUsage: {
        before: cpuUsage.before,
        after: cpuUsage.after,
        diffUser: cpuUsage.after.user - cpuUsage.before.user,
        diffSystem: cpuUsage.after.system - cpuUsage.before.system
      }
    },
    statistics: {
      mean,
      median,
      stdDev,
      p95,
      p99
    }
  };
}

/**
 * Сохраняет результаты в JSON-файл
 * @param {Object} results - Объект с результатами
 * @param {string} outputPath - Путь для сохранения результатов
 */
export async function saveResults(results, outputPath) {
  // Реализация для Deno
  if (typeof Deno !== 'undefined') {
    try {
      // Создаем директорию, если она не существует
      const dirPath = new URL('.', 'file://' + outputPath).pathname;
      try {
        Deno.mkdirSync(dirPath, { recursive: true });
      } catch (error) {
        if (!(error instanceof Deno.errors.AlreadyExists)) {
          throw error;
        }
      }
      
      // Записываем результаты в файл
      Deno.writeTextFileSync(outputPath, JSON.stringify(results, null, 2));
      console.log(`Результаты сохранены в ${outputPath}`);
    } catch (e) {
      console.error("Ошибка при сохранении результатов:", e);
    }
  } 
  // Реализация для Node.js и Bun
  else if (typeof process !== 'undefined') {
    try {
      // Динамический импорт модулей fs и path
      const { writeFileSync, mkdirSync, existsSync } = await import('fs');
      const { dirname } = await import('path');
      
      // Создаем директорию, если она не существует
      const dir = dirname(outputPath);
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
      }
      
      // Записываем результаты в файл
      writeFileSync(outputPath, JSON.stringify(results, null, 2));
      console.log(`Результаты сохранены в ${outputPath}`);
    } catch (e) {
      console.error("Ошибка при сохранении результатов:", e);
    }
  } else {
    console.error("Метод saveResults не реализован для данного рантайма");
  }
} 