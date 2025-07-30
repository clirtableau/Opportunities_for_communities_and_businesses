import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Функція для входу в Tableau та отримання сесії ---
def get_tableau_session(username, password):
    """
    Створює сесію, логіниться в Tableau Public і повертає
    автентифікований об'єкт сесії.
    """
    session = requests.Session()
    login_url = "https://public.tableau.com/auth/login"

    # 1. Перший GET-запит, щоб отримати початковий XSRF-TOKEN в cookie
    try:
        session.get(login_url, timeout=30)
        initial_xsrf_token = session.cookies.get('XSRF-TOKEN')
        if not initial_xsrf_token:
            raise ValueError("Не вдалося отримати початковий XSRF-TOKEN.")
    except requests.RequestException as e:
        print(f"Помилка при отриманні сторінки входу: {e}")
        return None

    # 2. Готуємо дані та заголовки для POST-запиту на вхід
    login_payload = {
        'username': username,
        'password': password,
        'workgroup': '',
        'csrf_token': initial_xsrf_token,
    }
    
    headers = {
        'X-XSRF-TOKEN': initial_xsrf_token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }

    # 3. Відправляємо POST-запит, щоб залогінитись
    try:
        login_response = session.post(login_url, data=login_payload, headers=headers, timeout=30)
        login_response.raise_for_status()
        
        # Перевіряємо, чи успішний вхід (Tableau повертає JSON з полем 'redirectPath')
        if 'redirectPath' not in login_response.json():
             raise ValueError("Відповідь Tableau не містить ознаки успішного входу.")
             
        return session # Повертаємо сесію з новими, автентифікованими cookie
        
    except requests.RequestException as e:
        print(f"Помилка під час запиту на вхід: {e}")
        print(f"Відповідь сервера: {login_response.text if 'login_response' in locals() else 'Немає відповіді'}")
        return None
    except ValueError as e:
        print(f"Помилка логіки входу: {e}")
        return None


# --- Головний ендпоінт для запуску оновлення ---
@app.route('/refresh-tableau', methods=['POST'])
def refresh_tableau():
    # 1. Зчитуємо секрети та налаштування зі змінних середовища Render
    my_api_key = os.environ.get("MY_API_KEY")
    tableau_username = os.environ.get("TABLEAU_USERNAME")
    tableau_password = os.environ.get("TABLEAU_PASSWORD")
    post_url = os.environ.get("TABLEAU_POST_URL")
    workbook_id = os.environ.get("TABLEAU_WORKBOOK_ID")
    
    # Перевірка безпеки
    if request.headers.get('X-API-Key') != my_api_key:
        return jsonify({"error": "Unauthorized"}), 401

    # Перевірка, чи всі змінні налаштовані
    if not all([tableau_username, tableau_password, post_url, workbook_id]):
        return jsonify({"error": "Server is not configured. Missing environment variables."}), 500
        
    # 2. Отримуємо нову сесію Tableau, залогінившись
    print("Спроба входу в Tableau...")
    tableau_session = get_tableau_session(tableau_username, tableau_password)
    
    if not tableau_session:
        return jsonify({"error": "Не вдалося увійти в Tableau. Перевірте логін/пароль та логи на Render."}), 500
    print("Вхід в Tableau успішний.")

    # 3. Готуємо та відправляємо запит на оновлення, використовуючи нову сесію
    try:
        refresh_xsrf_token = tableau_session.cookies.get('XSRF-TOKEN')
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            'X-XSRF-TOKEN': refresh_xsrf_token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }
        payload = {"workbookId": workbook_id}

        print("Надсилаю запит на оновлення...")
        response = tableau_session.post(post_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        print("Запит на оновлення успішно надіслано.")
        return jsonify({
            "status": "success", 
            "message": "Refresh request sent to Tableau successfully.",
            "tableau_response": response.json()
        })

    except requests.exceptions.RequestException as e:
        error_message = f"Failed to send refresh request to Tableau: {e}"
        print(error_message)
        return jsonify({"error": error_message}), 500


# --- Допоміжний ендпоінт для перевірки роботи сервісу ---
@app.route('/')
def index():
    return "Tableau Refresh Service is running!"
