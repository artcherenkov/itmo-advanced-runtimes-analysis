// Простой HTTP-сервер на Bun

const PORT = process.env.PORT || 3003;

const server = Bun.serve({
  port: PORT,
  fetch(req) {
    const url = new URL(req.url);
    
    if (url.pathname === '/ping') {
      return new Response('pong', {
        status: 200,
        headers: {
          'Content-Type': 'text/plain',
        },
      });
    } else {
      return new Response('Not Found', {
        status: 404,
      });
    }
  },
  error() {
    return new Response('Произошла ошибка', { status: 500 });
  },
});

console.log(`Сервер запущен на порту ${PORT}`);

// Обработка завершения
process.on('SIGINT', () => {
  console.log('Получен SIGINT, закрываем сервер...');
  server.stop();
  console.log('Сервер остановлен');
});

process.on('SIGTERM', () => {
  console.log('Получен SIGTERM, закрываем сервер...');
  server.stop();
  console.log('Сервер остановлен');
}); 