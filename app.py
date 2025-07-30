import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Функція для вилучення XSRF-TOKEN з cookie ---
# Tableau вимагає цей токен не тільки в cookie, але і в заголовку X-XSRF-TOKEN
def get_xsrf_token_from_cookie(cookie_string):
    if not cookie_string:
        return None
    try:
        # Розділяємо рядок cookie на окремі частини
        cookies = cookie_string.split('; ')
        for cookie in cookies:
            if cookie.startswith('XSRF-TOKEN='):
                return cookie.split('=')[1]
        return None
    except Exception:
        return None

# --- Головний ендпоінт для запуску оновлення ---
@app.route('/refresh-tableau', methods=['POST'])
def refresh_tableau():
    # 1. Зчитуємо всі наші секрети та налаштування зі змінних середовища Render
    my_api_key = os.environ.get("MY_API_KEY")
    post_url = os.environ.get("TABLEAU_POST_URL")
    cookie_header = os.environ.get("TABLEAU_HEADERS_COOKIE")
    workbook_id = os.environ.get("TABLEAU_WORKBOOK_ID")
    
    # Перевірка безпеки: чи надіслав Apps Script правильний ключ?
    if request.headers.get('X-API-Key') != my_api_key:
        return jsonify({"error": "Unauthorized"}), 401

    # Перевірка, чи всі змінні середовища налаштовані на Render
    if not all([post_url, cookie_header, workbook_id]):
        return jsonify({"error": "Server is not configured. Missing environment variables."}), 500
        
    xsrf_token = get_xsrf_token_from_cookie(cookie_header)
    if not xsrf_token:
        return jsonify({"error": "Failed to parse XSRF-TOKEN from cookie"}), 500

    # 2. Готуємо заголовки та тіло запиту для Tableau
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'Cookie': cookie_header,
        'X-XSRF-TOKEN': xsrf_token, # Дуже важливий заголовок
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    
    # Тіло запиту (payload). Tableau очікує ID воркбука
    payload = {
        "workbookId": workbook_id
    }

    # 3. Відправляємо запит на сервер Tableau
    try:
        response = requests.post(post_url, headers=headers, json=payload)
        response.raise_for_status() # Генерує помилку, якщо статус-код відповіді > 400

        # Повертаємо успішну відповідь
        return jsonify({
            "status": "success", 
            "message": "Refresh request sent to Tableau successfully.",
            "tableau_response": response.json() # Повертаємо відповідь від Tableau
        })

    except requests.exceptions.RequestException as e:
        # Повертаємо помилку, якщо запит до Tableau не вдався
        return jsonify({"error": f"Failed to send request to Tableau: {e}"}), 500


# --- Допоміжний ендпоінт для перевірки роботи сервісу ---
@app.route('/')
def index():
    return "Tableau Refresh Service is running!"
