import os
import requests
import time
from flask import Flask, request, jsonify

# Імпортуємо бібліотеки для Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# --- Оновлена функція для входу в Tableau за допомогою Selenium ---
def get_tableau_session(username, password):
    """
    Запускає віртуальний браузер, логіниться в Tableau і повертає
    автентифікований об'єкт сесії requests.
    """
    print("Налаштування віртуального браузера...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск без графічного інтерфейсу
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

    try:
        # Використовуємо webdriver-manager для автоматичного завантаження драйвера
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Браузер запущено.")
        
        login_url = "https://public.tableau.com/auth/login"
        print(f"Переходжу на сторінку входу: {login_url}")
        driver.get(login_url)
        time.sleep(4) # Даємо час на виконання JavaScript та завантаження сторінки

        # 1. Знаходимо поля та вводимо логін і пароль
        print("Вводжу логін та пароль...")
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        
        # 2. Знаходимо та натискаємо кнопку входу
        # Використовуємо XPath для надійного пошуку кнопки
        driver.find_element(By.XPATH, "//button[normalize-space()='Sign In']").click()
        print("Натиснув кнопку 'Sign In'.")
        time.sleep(6) # Чекаємо на завершення процесу входу

        # 3. Перевіряємо, чи вхід був успішним (наприклад, перевіряючи URL)
        if "auth/login" in driver.current_url:
            raise ValueError("Вхід не вдався. Залишився на сторінці логіну. Перевірте логін/пароль.")
        print("Вхід виглядає успішним.")

        # 4. Створюємо сесію requests та переносимо в неї автентифіковані cookie
        session = requests.Session()
        selenium_cookies = driver.get_cookies()
        for cookie in selenium_cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        
        return session

    except Exception as e:
        print(f"Сталася помилка в процесі Selenium: {e}")
        return None
    finally:
        if 'driver' in locals():
            driver.quit()
            print("Браузер закрито.")


# --- Головний ендпоінт для запуску оновлення (залишається майже без змін) ---
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
        if not refresh_xsrf_token:
            raise ValueError("Не вдалося знайти XSRF-TOKEN в сесії після входу.")

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

    except Exception as e:
        error_message = f"Failed to send refresh request to Tableau: {e}"
        print(error_message)
        return jsonify({"error": error_message}), 500


# --- Допоміжний ендпоінт для перевірки роботи сервісу ---
@app.route('/')
def index():
    return "Tableau Refresh Service is running!"
