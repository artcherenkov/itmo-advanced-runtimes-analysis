const http = require('http');

const PORT = process.env.PORT || 3000;

// Создаем HTTP сервер
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

// Запускаем сервер
server.listen(PORT, () => {
  console.log(`Сервер запущен на порту ${PORT}`);
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