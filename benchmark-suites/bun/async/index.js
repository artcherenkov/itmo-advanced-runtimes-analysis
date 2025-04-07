import { file } from 'bun';
import crypto from 'crypto';

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
  const data = Buffer.from(crypto.randomBytes(FILE_OPERATION_SIZE));
  
  // Запись данных в файл (используем Bun-специфичные API)
  await Bun.write(tempFileName, data);
  
  // Чтение файла
  const readData = await file(tempFileName).arrayBuffer();
  
  // Удаление временного файла
  try {
    await Bun.file(tempFileName).remove();
  } catch (error) {
    console.error(`Ошибка при удалении файла: ${error.message}`);
  }
  
  return data.length;
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

// Создаем HTTP сервер с использованием Bun
const server = Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    
    if (url.pathname === "/async-bench") {
      try {
        const startTime = performance.now();
        
        // Выполняем параллельные асинхронные задачи
        const results = await runParallelTasks();
        
        const endTime = performance.now();
        const duration = endTime - startTime; // в миллисекундах
        
        // Отправляем ответ
        return new Response(
          JSON.stringify({
            success: true,
            tasks_completed: results.length,
            duration_ms: duration
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json"
            }
          }
        );
      } catch (error) {
        // Обрабатываем ошибки
        return new Response(
          JSON.stringify({
            success: false,
            error: error.message
          }),
          {
            status: 500,
            headers: {
              "Content-Type": "application/json"
            }
          }
        );
      }
    } else {
      return new Response("Not Found", { status: 404 });
    }
  }
});

console.log(`Асинхронный бенчмарк-сервер запущен на порту ${PORT}`); 