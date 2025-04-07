// Минимальный HTTP-сервер для измерения времени холодного старта Bun

// Захватываем начальное время запуска (T0 считается в скрипте)
const startTime = Date.now();

// Создаем HTTP-сервер используя встроенный Bun.serve
const server = Bun.serve({
  port: process.env.PORT || 3000,
  fetch(req) {
    // Отправляем простой JSON-ответ
    return new Response(
      JSON.stringify({ status: 'ok' }),
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
  },
  error(error) {
    console.error(`Ошибка сервера: ${error.message}`);
    process.exit(1);
  }
});

// Выводим сообщение о готовности
const readyTime = Date.now();
console.log(`READY_TIMESTAMP:${readyTime}`);
console.log(`HTTP-сервер запущен на порту ${server.port}`); 