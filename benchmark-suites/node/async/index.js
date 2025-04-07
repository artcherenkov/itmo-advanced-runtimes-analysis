const http = require('http');
const fs = require('fs/promises');
const { promisify } = require('util');
const crypto = require('crypto');

const PORT = parseInt(process.env.PORT || "3000");
const PARALLEL_TASKS = parseInt(process.env.PARALLEL_TASKS || "5");
const FILE_OPERATION_SIZE = parseInt(process.env.FILE_OPERATION_SIZE || String(1024 * 512)); // 512KB по умолчанию
const DELAY_MS = parseInt(process.env.DELAY_MS || "50"); // задержка в мс

// Эмуляция запроса к внешнему API
async function mockExternalApiCall() {
  // Эмулируем задержку сети
  return new Promise(resolve => {
    setTimeout(() => {
      resolve({ status: 'success', timestamp: Date.now() });
    }, DELAY_MS);
  });
}

// Асинхронная операция чтения/записи файла
async function fileOperation() {
  const tempFileName = `/tmp/async_bench_${Date.now()}_${Math.random().toString(36).substring(7)}.tmp`;
  
  // Генерация случайных данных
  const data = crypto.randomBytes(FILE_OPERATION_SIZE);
  
  // Запись данных в файл
  await fs.writeFile(tempFileName, data);
  
  // Чтение файла
  const readData = await fs.readFile(tempFileName);
  
  // Удаление временного файла
  await fs.unlink(tempFileName);
  
  return readData.length;
}

// Выполнение нескольких асинхронных задач параллельно
async function runParallelTasks() {
  const tasks = [];
  
  for (let i = 0; i < PARALLEL_TASKS; i++) {
    if (i % 3 === 0) {
      // Каждую третью задачу делаем операцией с файлом
      tasks.push(fileOperation());
    } else if (i % 3 === 1) {
      // Каждую вторую задачу делаем эмуляцией API-запроса
      tasks.push(mockExternalApiCall());
    } else {
      // Остальные задачи делаем случайной задержкой
      tasks.push(new Promise(resolve => {
        setTimeout(() => resolve(Date.now()), Math.random() * DELAY_MS);
      }));
    }
  }
  
  // Запускаем все задачи параллельно
  return Promise.all(tasks);
}

// Создаем HTTP сервер
const server = http.createServer(async (req, res) => {
  if (req.url === '/async-bench') {
    try {
      const startTime = process.hrtime.bigint();
      
      // Выполняем параллельные асинхронные задачи
      const results = await runParallelTasks();
      
      const endTime = process.hrtime.bigint();
      const duration = Number(endTime - startTime) / 1_000_000; // в миллисекундах
      
      // Отправляем ответ
      res.statusCode = 200;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({
        success: true,
        tasks_completed: results.length,
        duration_ms: duration
      }));
    } catch (error) {
      // Обрабатываем ошибки
      res.statusCode = 500;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({
        success: false,
        error: error.message
      }));
    }
  } else {
    res.statusCode = 404;
    res.end('Not Found');
  }
});

// Запускаем сервер
server.listen(PORT, () => {
  console.log(`Асинхронный бенчмарк-сервер запущен на порту ${PORT}`);
});

// Обработка сигналов для корректного завершения
process.on('SIGTERM', () => {
  console.log('Получен SIGTERM, закрываем сервер...');
  server.close(() => {
    console.log('Сервер остановлен');
  });
});

process.on('SIGINT', () => {
  console.log('Получен SIGINT, закрываем сервер...');
  server.close(() => {
    console.log('Сервер остановлен');
  });
}); 