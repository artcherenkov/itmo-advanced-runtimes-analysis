/**
 * Бенчмарк HTTP нагрузочного тестирования для Node.js - ESM версия
 */
import http from 'http';
import { exec } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import util from 'util';

// Преобразуем exec в Promise-версию
const execAsync = util.promisify(exec);

// Получаем текущую директорию через ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Опции по умолчанию для бенчмарка
const DEFAULT_PORT = parseInt(process.env.PORT) || 3030;
const DEFAULT_THREADS = parseInt(process.env.WRK_THREADS) || 4;
const DEFAULT_CONNECTIONS = parseInt(process.env.WRK_CONNECTIONS) || 100;
const DEFAULT_DURATION = process.env.WRK_DURATION || '30s';

/**
 * Создает простой HTTP сервер
 * @returns {http.Server} HTTP сервер
 */
function createServer() {
  const server = http.createServer((req, res) => {
    if (req.url === '/ping') {
      res.statusCode = 200;
      res.setHeader('Content-Type', 'text/plain');
      res.end('pong');
    } else {
      res.statusCode = 404;
      res.end('Not Found');
    }
  });

  return server;
}

/**
 * Запускает wrk инструмент для нагрузочного тестирования
 * @param {number} port - Порт сервера
 * @param {Object} options - Опции для wrk
 * @returns {Object} Результаты тестирования
 */
async function runWrkBenchmark(port, options = {}) {
  const {
    threads = DEFAULT_THREADS,
    connections = DEFAULT_CONNECTIONS,
    duration = DEFAULT_DURATION
  } = options;

  const url = `http://localhost:${port}/ping`;
  const wrkCommand = `wrk -t${threads} -c${connections} -d${duration} --latency ${url}`;
  
  console.log(`Выполнение команды: ${wrkCommand}`);
  const { stdout } = await execAsync(wrkCommand);
  
  console.log("Результаты wrk:");
  console.log(stdout);
  
  // Извлекаем метрики из вывода wrk
  const requestsPerSec = parseFloat(stdout.match(/Requests\/sec:\s+([0-9.]+)/)?.[1] || '0');
  const latencyAvg = stdout.match(/Latency\s+([0-9.]+\w+)/)?.[1] || '0ms';
  const latencyP50 = stdout.match(/50%\s+([0-9.]+\w+)/)?.[1] || '0ms';
  const latencyP90 = stdout.match(/90%\s+([0-9.]+\w+)/)?.[1] || '0ms';
  const latencyP99 = stdout.match(/99%\s+([0-9.]+\w+)/)?.[1] || '0ms';
  const transferRate = stdout.match(/Transfer\/sec:\s+([0-9.]+\w+)/)?.[1] || '0KB';
  
  // Извлечение данных для расчета ошибок
  const totalRequests = parseInt(stdout.match(/(\d+)\s+requests/)?.[1] || '0', 10);
  const nonSuccessResponses = parseInt(stdout.match(/Non-2xx\s+responses:\s+(\d+)/)?.[1] || '0', 10);
  
  // Расчет процента ошибок
  const errorRate = nonSuccessResponses ? nonSuccessResponses / totalRequests : 0;
  
  return {
    timestamp: new Date().toISOString(),
    requestsPerSecond: requestsPerSec,
    latency: {
      average: latencyAvg,
      p50: latencyP50,
      p90: latencyP90,
      p99: latencyP99
    },
    transferRate,
    errorRate,
    totalRequests,
    nonSuccessResponses,
    benchmark: {
      threads,
      connections,
      duration
    }
  };
}

/**
 * Запускает бенчмарк HTTP сервера
 */
async function runBenchmark() {
  console.log(`Запуск HTTP нагрузочного тестирования для Node.js (${process.version})`);
  
  // Получаем параметры из переменных окружения
  const port = DEFAULT_PORT;
  const threads = DEFAULT_THREADS;
  const connections = DEFAULT_CONNECTIONS;
  const duration = DEFAULT_DURATION;
  
  console.log(`- Порт: ${port}`);
  console.log(`- Потоки wrk: ${threads}`);
  console.log(`- Соединения: ${connections}`);
  console.log(`- Продолжительность: ${duration}`);
  console.log(`- Контейнер: ${process.env.CONTAINER === 'true' ? 'Да' : 'Нет'}`);
  
  // Создаем и запускаем сервер
  const server = createServer();
  
  console.log(`Запуск HTTP сервера на порту ${port}...`);
  server.listen(port);
  
  // Даем серверу время на запуск
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  console.log("Сервер запущен. Начинаем нагрузочное тестирование...");
  
  try {
    // Запускаем wrk бенчмарк
    const results = await runWrkBenchmark(port, { 
      threads, 
      connections, 
      duration 
    });
    
    // Создаем имя файла для результатов
    const resultsFilename = path.join(
      __dirname, 
      '../../../results', 
      `node_http_t${threads}_c${connections}_${Date.now()}.json`
    );
    
    // Сохраняем результаты
    await fs.mkdir(path.dirname(resultsFilename), { recursive: true }).catch(() => {});
    await fs.writeFile(resultsFilename, JSON.stringify(results, null, 2));
    
    console.log('\nБенчмарк завершен!');
    console.log(`Запросов в секунду: ${results.requestsPerSecond.toFixed(2)}`);
    console.log(`Средняя задержка: ${results.latency.average}`);
    console.log(`Задержка P99: ${results.latency.p99}`);
    console.log(`Процент ошибок: ${(results.errorRate * 100).toFixed(2)}%`);
    console.log(`\nРезультаты сохранены в: ${resultsFilename}`);
    
  } catch (error) {
    console.error("Ошибка при выполнении бенчмарка:", error);
  } finally {
    // Закрываем сервер
    server.close();
    console.log("HTTP сервер остановлен.");
  }
}

// Запускаем бенчмарк
runBenchmark().catch(err => {
  console.error("Критическая ошибка при выполнении бенчмарка:", err);
  process.exit(1);
}); 