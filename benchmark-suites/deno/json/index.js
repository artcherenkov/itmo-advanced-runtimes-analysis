/**
 * Бенчмарк парсинга и сериализации JSON для Deno
 */
import { join } from "https://deno.land/std/path/mod.ts";
import { benchmark } from '../utils/metrics.js';
import { preventOptimization } from '../utils/deoptimize.js';

/**
 * Генерирует большой JSON-объект для тестирования
 * @param {number} size - Количество элементов в массиве
 * @returns {Object} - Большой JSON-объект
 */
function generateLargeJsonObject(size) {
  const result = {
    items: [],
    metadata: {
      createdAt: new Date().toISOString(),
      version: "1.0.0",
      tags: ["benchmark", "json", "deno", "javascript"],
      settings: {
        enabled: true,
        timeout: 5000,
        retries: 3,
        parameters: {
          a: 1.234,
          b: "string value",
          c: false,
          d: null
        }
      }
    }
  };
  
  for (let i = 0; i < size; i++) {
    result.items.push({
      id: i,
      uuid: `uuid-${Math.random().toString(36).substring(2, 15)}`,
      name: `Item ${i}`,
      value: Math.random() * 1000,
      isActive: i % 3 === 0,
      tags: [`tag-${i % 5}`, `category-${i % 10}`],
      nested: {
        level1: {
          level2: {
            level3: {
              value: `Nested value ${i}`,
              created: new Date(Date.now() + i * 1000).toISOString()
            }
          }
        }
      }
    });
  }
  
  return result;
}

/**
 * Функция для сериализации и десериализации JSON
 * @param {Object} jsonObj - JSON-объект для сериализации/десериализации
 * @returns {Object} - Результат десериализации
 */
function jsonParseStringify(jsonObj) {
  const stringified = JSON.stringify(jsonObj);
  return JSON.parse(stringified);
}

// Деоптимизированная версия функции
const jsonParseStringifyDeoptimized = preventOptimization(jsonParseStringify);

/**
 * Функция для глубокого клонирования с использованием JSON
 * @param {Object} obj - Объект для клонирования
 * @returns {Object} - Клонированный объект
 */
function deepCloneViaJson(obj) {
  return JSON.parse(JSON.stringify(obj));
}

// Деоптимизированная версия функции
const deepCloneViaJsonDeoptimized = preventOptimization(deepCloneViaJson);

/**
 * Запуск бенчмарка
 */
async function runBenchmark() {
  // Получаем входные параметры из аргументов командной строки или переменных окружения
  const objectSize = parseInt(Deno.env.get("JSON_OBJECT_SIZE")) || 1000;
  const operation = Deno.env.get("JSON_OPERATION") || 'parse-stringify';
  const iterations = parseInt(Deno.env.get("ITERATIONS")) || 30;
  
  console.log(`Запуск бенчмарка JSON для Deno (${Deno.version.deno})`);
  console.log(`- Размер объекта: ${objectSize} элементов`);
  console.log(`- Операция: ${operation}`);
  console.log(`- Количество итераций: ${iterations}`);
  console.log(`- Контейнер: ${Deno.env.get("CONTAINER") === 'true' ? 'Да' : 'Нет'}`);
  
  // Генерируем тестовый JSON-объект
  const testObject = generateLargeJsonObject(objectSize);
  
  // Выбираем функцию для тестирования
  let fnToTest;
  let description;
  
  if (operation === 'parse-stringify') {
    fnToTest = jsonParseStringifyDeoptimized;
    description = 'сериализация и десериализация JSON';
  } else {
    fnToTest = deepCloneViaJsonDeoptimized;
    description = 'глубокое клонирование через JSON';
  }
  
  console.log(`Используется ${description} с деоптимизацией`);
  console.log(`Размер JSON: примерно ${Math.round(JSON.stringify(testObject).length / 1024)} КБ`);
  
  // Настраиваем параметры бенчмарка
  const benchmarkOptions = {
    iterations,
    warmupIterations: 3,
    experiment: `json_${operation}_size${objectSize}`,
    detailedMetrics: true,
    outputPath: '/app/results/' + `deno_json_${operation}_size${objectSize}_${Date.now()}.json`
  };
  
  // Запускаем бенчмарк
  const results = await benchmark(fnToTest, [testObject], benchmarkOptions);
  
  console.log('\nБенчмарк завершен!');
  console.log(`Среднее время выполнения: ${(results.statistics.mean / 1_000_000).toFixed(3)} мс`);
  console.log(`Медиана времени выполнения: ${(results.statistics.median / 1_000_000).toFixed(3)} мс`);
  console.log(`Стандартное отклонение: ${(results.statistics.stdDev / 1_000_000).toFixed(3)} мс`);
  console.log(`95-й процентиль: ${(results.statistics.p95 / 1_000_000).toFixed(3)} мс`);
  
  // Выводим информацию о потреблении памяти
  const memoryDiff = results.metrics.memoryUsage.diff;
  console.log('\nИзменение использования памяти:');
  console.log(`RSS: ${(memoryDiff.rss / (1024 * 1024)).toFixed(2)} МБ`);
  console.log(`Heap Total: ${(memoryDiff.heapTotal / (1024 * 1024)).toFixed(2)} МБ`);
  console.log(`Heap Used: ${(memoryDiff.heapUsed / (1024 * 1024)).toFixed(2)} МБ`);
  
  console.log(`\nРезультаты сохранены в: ${benchmarkOptions.outputPath}`);
  
  return results;
}

// Запускаем бенчмарк
runBenchmark().catch(err => {
  console.error("Ошибка при выполнении бенчмарка:", err);
  Deno.exit(1);
}); 