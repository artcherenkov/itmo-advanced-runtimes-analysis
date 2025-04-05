/**
 * Стандартный интерфейс метрик для всех рантаймов
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
function formatMetrics(runtime, version, experiment, executionTimes, memoryUsage, cpuUsage) {
  // Вычисление статистики
  const mean = executionTimes.reduce((a, b) => a + b, 0) / executionTimes.length;
  const sorted = [...executionTimes].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const stdDev = Math.sqrt(
    executionTimes.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / executionTimes.length
  );
  const p95 = sorted[Math.floor(sorted.length * 0.95)];
  const p99 = sorted[Math.floor(sorted.length * 0.99)];
  
  return {
    runtime,
    version,
    experiment,
    timestamp: new Date().toISOString(),
    environment: {
      os: process.platform,
      container: process.env.CONTAINER === 'true',
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
function saveResults(results, outputPath) {
  const fs = require('fs');
  const path = require('path');
  
  // Создаем директорию, если она не существует
  const dir = path.dirname(outputPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  // Записываем результаты в файл
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
  console.log(`Результаты сохранены в ${outputPath}`);
}

module.exports = {
  formatMetrics,
  saveResults
}; 