from flask import Flask, request, jsonify
import os

# Створюємо Flask-додаток
app = Flask(__name__)

# Отримуємо ключ API зі змінних середовища Render.
# Це безпечніше, ніж зберігати його в коді.
# Якщо змінна не знайдена, використовується значення за замовчуванням.
SECRET_API_KEY = os.environ.get('MY_SECRET_API_KEY', 'default_secret_key')

# Додамо головний маршрут для перевірки, що сервіс працює
@app.route('/')
def index():
    return "Python Web Service is running!"

# Наш основний ендпоінт для тригера
@app.route('/trigger', methods=['POST'])
def trigger_script():
    # --- Блок безпеки ---
    auth_header = request.headers.get('X-API-Key')
    if auth_header != SECRET_API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # --- Основна логіка ---
    try:
        data = request.get_json()
        user_name = data.get('name', 'Anonymous') # .get() безпечніший

        result_message = f"Hello from Render, {user_name}! Your script was triggered."
        return jsonify({"status": "success", "message": result_message})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500