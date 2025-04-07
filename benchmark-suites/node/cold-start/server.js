// Минимальный HTTP-сервер для измерения времени холодного старта
const http = require('http');

// Захватываем начальное время запуска (T0 считается в скрипте)
const startTime = Date.now();

// Создаем HTTP-сервер
const server = http.createServer((req, res) => {
  // Установка заголовков ответа
  res.setHeader('Content-Type', 'application/json');
  
  // Отправляем простой JSON-ответ
  res.end(JSON.stringify({ status: 'ok' }));
});

// Обработка ошибок сервера
server.on('error', (err) => {
  console.error(`Ошибка сервера: ${err.message}`);
  process.exit(1);
});

// Порт для HTTP-сервера
const PORT = process.env.PORT || 3000;

// Запускаем сервер и выводим сообщение о готовности
server.listen(PORT, () => {
  const readyTime = Date.now();
  console.log(`READY_TIMESTAMP:${readyTime}`);
  console.log(`HTTP-сервер запущен на порту ${PORT}`);
}); 