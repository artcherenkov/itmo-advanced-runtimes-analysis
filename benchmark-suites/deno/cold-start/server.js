// Минимальный HTTP-сервер для измерения времени холодного старта Deno

// Захватываем начальное время запуска (T0 считается в скрипте)
const startTime = Date.now();

// Импортируем необходимые модули
import { serve } from "https://deno.land/std/http/server.ts";

// Создаем HTTP-сервер используя Deno serve API
const handler = (req) => {
  // Отправляем простой JSON-ответ
  return new Response(
    JSON.stringify({ status: 'ok' }),
    {
      headers: {
        'Content-Type': 'application/json'
      }
    }
  );
};

// Определяем порт
const port = parseInt(Deno.env.get("PORT") || "3000");

// Запускаем сервер
const server = serve(handler, { port: port });

// Выводим сообщение о готовности
const readyTime = Date.now();
console.log(`READY_TIMESTAMP:${readyTime}`);
console.log(`HTTP-сервер запущен на порту ${port}`); 