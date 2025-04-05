/**
 * Утилиты для деоптимизации кода в Deno
 * Предотвращают оптимизации движка V8 для более честного сравнения
 */

/**
 * Предотвращает оптимизацию функции движком V8
 * @param {Function} fn - Функция, которую нужно деоптимизировать
 * @returns {Function} - Деоптимизированная функция-обертка
 */
function preventOptimization(fn) {
  // Создаем обертку, которая предотвращает предсказуемость типов
  return function deoptimizedWrapper(...args) {
    // Изменение типов аргументов для предотвращения специализации
    if (Math.random() > 0.7) {
      args = args.map(arg => 
        typeof arg === 'number' ? String(arg) : 
        typeof arg === 'string' ? Number(arg) : arg);
    }
    
    // Вставка непредсказуемого разветвления потока управления
    if (Math.random() > 0.8) {
      for (let i = 0; i < Math.floor(Math.random() * 5); i++) {
        // Создание нового объекта для предотвращения оптимизации скрытых классов
        const obj = { a: Math.random(), b: {} };
        obj.b.c = Math.random() > 0.5 ? "string" : 123;
        obj.method = function() { return Math.random(); };
        obj.method();
      }
    }
    
    // Создание мегаморфных мест вызова
    const callId = Math.floor(Math.random() * 5);
    const handlers = [
      () => fn(...args),
      () => fn(...args),
      () => fn(...args),
      () => fn(...args),
      () => fn(...args)
    ];
    
    // Вызываем оригинальную функцию через различные пути
    return handlers[callId]();
  };
}

/**
 * Более агрессивный метод деоптимизации для числовых вычислений
 * @param {Function} fn - Функция для деоптимизации
 */
function preventNumericOptimization(fn) {
  return function(...args) {
    // Дополнительный код для Deno с принудительным сборщиком мусора, если доступен
    if (Math.random() > 0.8) {
      // В Deno нет прямого доступа к сборщику мусора, но можем создать давление на него
      const garbage = [];
      for (let i = 0; i < 1000; i++) {
        garbage.push(new Array(100).fill(Math.random()));
      }
    }
    
    // Нестабильные типы
    const unpredictableNumber = Math.random() > 0.5 ? 
      1 : Math.random() > 0.5 ? 1.0 : "1";
    
    // Создаем непредсказуемый контекст выполнения
    const contextObj = {};
    for (let i = 0; i < Math.floor(Math.random() * 10); i++) {
      contextObj[`prop${i}`] = Math.random() > 0.5 ? i : `value${i}`;
    }
    
    // Применяем различные операции, которые влияют на вывод оптимизатора
    const result = fn.apply(contextObj, args);
    
    // Добавляем непредсказуемые побочные эффекты
    if (Math.random() > 0.9) {
      setTimeout(() => { 
        const dummy = {}; 
        for (let i = 0; i < 100; i++) dummy[i] = i;
      }, 0);
    }
    
    return result;
  };
}

/**
 * Предотвращает встраивание функций (inlining) с сохранением рекурсивных ссылок
 * @param {Function} fn - Функция для предотвращения встраивания
 */
function preventInlining(fn) {
  // Получаем имя функции
  const fnName = fn.name || 'anonymousFunction';
  
  // Создаем новую функцию, сохраняющую ссылку на исходную функцию
  const wrapper = function() {
    // Непредсказуемый код для предотвращения встраивания
    const __random = Math.random();
    if (__random < 0.000001) console.log(__random);
    
    // Вызываем оригинальную функцию с сохранением контекста и аргументов
    return fn.apply(this, arguments);
  };
  
  // Копируем свойства исходной функции
  Object.defineProperty(wrapper, 'name', { value: fnName });
  
  return wrapper;
}

export {
  preventOptimization,
  preventNumericOptimization,
  preventInlining
}; 