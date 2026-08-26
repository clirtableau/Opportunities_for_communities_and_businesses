from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests

URL = "https://www.kmu.gov.ua/diyalnist/mizhnarodna-dopomoga/pereliki-zareyestrovanih-proektiv-z-planami-zakupivel"
STATE_FILE = "last_known_url.txt"

def get_current_file_url():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        page.wait_for_load_state("networkidle")
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("a", href=True):
        text = link.get_text(strip=True)
        if "Перелік проектів МТД" in text:
            return link["href"]
    return None

def get_last_known_url():
    try:
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_current_url(url):
    with open(STATE_FILE, "w") as f:
        f.write(url)

current_url = get_current_file_url()
if current_url is None:
    raise ValueError("Не вдалося знайти посилання на файл — перевір текст пошуку")

last_url = get_last_known_url()

if current_url != last_url:
    print(f"Файл оновився: {current_url}")
    file_response = requests.get(current_url)
    with open("latest_mtd.xlsx", "wb") as f:
        f.write(file_response.content)
    save_current_url(current_url)
else:
    print("Оновлень немає")
