/**
 * Викликає Python-скрипт на Render для оновлення дашборду Tableau.
 */
function triggerTableauRefresh() {
  // 1. Вставте сюди URL вашого сервісу на Render
  //    Формат: https://your-app-name.onrender.com/refresh-tableau
  const renderUrl = "https://your-app-name.onrender.com/refresh-tableau"; 

  // 2. Вставте сюди ваш секретний ключ, який ви вказали на Render
  const apiKey = "super-secret-12345";

  // 3. (Опціонально) Дані, які можна передати в Python.
  //    Наш поточний Python-скрипт не використовує ці дані, але це
  //    може знадобитися в майбутньому.
  const payloadData = {
    'source': 'Google Sheets Trigger',
    'user': Session.getActiveUser().getEmail()
  };

  // Налаштування для HTTP POST-запиту
  const options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': {
      // Цей заголовок використовується для авторизації в нашому Python-скрипті
      'X-API-Key': apiKey
    },
    // Перетворюємо об'єкт JavaScript в рядок формату JSON
    'payload': JSON.stringify(payloadData),
    // Важливо! Дозволяє нам бачити повний текст помилки, якщо вона станеться
    'muteHttpExceptions': true 
  };

  try {
    // Виконуємо запит
    const response = UrlFetchApp.fetch(renderUrl, options);
    
    const responseCode = response.getResponseCode();
    const responseBody = response.getContentText();
    
    // Виводимо результат у логи Apps Script (Ctrl + Enter)
    Logger.log(`HTTP Status Code: ${responseCode}`);
    Logger.log(`Response Body: ${responseBody}`);

    // Показуємо спливаюче вікно з результатом
    if (responseCode === 200) {
      const jsonResponse = JSON.parse(responseBody);
      SpreadsheetApp.getUi().alert(`✅ Успіх!\n\nПовідомлення від Python: ${jsonResponse.message}`);
    } else {
      SpreadsheetApp.getUi().alert(`❌ Помилка ${responseCode}\n\nВідповідь сервера:\n${responseBody}`);
    }
    
  } catch (e) {
    Logger.log(`Не вдалося виконати запит: ${e.toString()}`);
    SpreadsheetApp.getUi().alert(`Критична помилка:\n${e.toString()}`);
  }
}

/**
 * Додає кастомне меню в інтерфейс Google Таблиць
 * для ручного запуску оновлення.
 */
function onOpen() {
  SpreadsheetApp.getUi()
      .createMenu('Tableau')
      .addItem('Оновити дашборд', 'triggerTableauRefresh')
      .addToUi();
}
