/**
 * Утилиты для предотвращения оптимизаций функций в Deno
 * 
 * Эти функции помогают предотвратить оптимизации, которые могут быть применены
 * к функциям, что позволяет более точно измерять производительность алгоритмов.
 */

/**
 * Предотвращает inline-оптимизацию функции путем создания динамической функции,
 * которая вызывает указанную функцию.
 * 
 * @param {Function} fn - Функция, которую нужно защитить от inline-оптимизации
 * @returns {Function} - Wrapped функция
 */
export function preventInlining(fn) {
  // Создаем функцию динамически, чтобы предотвратить inline-оптимизацию
  const dynamicFn = new Function('fn', 'args', 'return fn.apply(this, args)');
  
  // Возвращаем wrapped функцию
  return function(...args) {
    return dynamicFn(fn, args);
  };
}

/**
 * Предотвращает оптимизации, связанные с числовыми операциями,
 * путем добавления незначительного шума к аргументам и результатам.
 * 
 * @param {Function} fn - Функция, для которой нужно предотвратить числовые оптимизации
 * @returns {Function} - Wrapped функция
 */
export function preventNumericOptimization(fn) {
  return function(...args) {
    // Добавляем незначительный шум к каждому числовому аргументу
    const noisyArgs = args.map(arg => {
      if (typeof arg === 'number') {
        // Добавляем очень маленький шум, который не влияет на результат,
        // но предотвращает некоторые оптимизации
        return arg + Number.EPSILON - Number.EPSILON;
      }
      return arg;
    });
    
    // Вызываем функцию с зашумленными аргументами
    const result = fn.apply(this, noisyArgs);
    
    // Если результат - число, добавляем незначительный шум к результату
    if (typeof result === 'number') {
      return result + Number.EPSILON - Number.EPSILON;
    }
    
    return result;
  };
}

/**
 * Предотвращает оптимизацию функции движком V8
 * @param {Function} fn - Функция, которую нужно деоптимизировать
 * @returns {Function} - Деоптимизированная функция-обертка
 */
export function preventOptimization(fn) {
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

// Экспорт по умолчанию всех функций
export default {
  preventOptimization,
  preventNumericOptimization,
  preventInlining
}; 