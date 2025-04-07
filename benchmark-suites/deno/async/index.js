// Импорты необходимых модулей
import { serve } from "https://deno.land/std/http/server.ts";

const PORT = parseInt(Deno.env.get("PORT") || "3000");
const PARALLEL_TASKS = parseInt(Deno.env.get("PARALLEL_TASKS") || "5");
const FILE_OPERATION_SIZE = parseInt(Deno.env.get("FILE_OPERATION_SIZE") || String(1024 * 512)); // 512KB по умолчанию
const DELAY_MS = parseInt(Deno.env.get("DELAY_MS") || "50"); // задержка в мс

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
  // Ограничение API crypto.getRandomValues - 65536 байт (64КБ)
  // Разбиваем на части по 64КБ
  const CHUNK_SIZE = 65536; // максимальный размер для crypto.getRandomValues
  const fullData = new Uint8Array(FILE_OPERATION_SIZE);
  
  // Заполняем массив по частям
  for (let offset = 0; offset < FILE_OPERATION_SIZE; offset += CHUNK_SIZE) {
    const length = Math.min(CHUNK_SIZE, FILE_OPERATION_SIZE - offset);
    const chunk = new Uint8Array(length);
    crypto.getRandomValues(chunk);
    fullData.set(chunk, offset);
  }
  
  // Запись данных в файл
  await Deno.writeFile(tempFileName, fullData);
  
  // Чтение файла
  const readData = await Deno.readFile(tempFileName);
  
  // Удаление временного файла
  await Deno.remove(tempFileName);
  
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

// Обработчик HTTP-запросов
async function handler(req) {
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

// Запускаем сервер
console.log(`Асинхронный бенчмарк-сервер запущен на порту ${PORT}`);
await serve(handler, { port: PORT }); 