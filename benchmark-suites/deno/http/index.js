// Простой HTTP-сервер на Deno

const PORT = Deno.env.get("PORT") || 3002;

const server = Deno.serve({ port: Number(PORT) }, (req) => {
  if (req.url.endsWith('/ping')) {
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
});

console.log(`Сервер запущен на порту ${PORT}`);

// Ожидаем прерывания сигналом для корректного завершения
Deno.addSignalListener("SIGINT", () => {
  console.log("Получен SIGINT, закрываем сервер...");
  server.shutdown();
  console.log("Сервер остановлен");
  Deno.exit();
});

Deno.addSignalListener("SIGTERM", () => {
  console.log("Получен SIGTERM, закрываем сервер...");
  server.shutdown();
  console.log("Сервер остановлен");
  Deno.exit();
}); 