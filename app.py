import requests
from bs4 import BeautifulSoup

URL = "https://www.kmu.gov.ua/mizhnarodna-tehnichna-dopomoga/perelik-zareiestrovanih-proiektiv-z-planami-zakupivel"
STATE_FILE = "last_known_url.txt"

def get_current_file_url():
    response = requests.get(URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Шукаємо посилання саме за текстом всередині <span>
    for link in soup.find_all("a", href=True):
        if "Перелік проєктів МТД" in link.get_text():
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
last_url = get_last_known_url()

if current_url != last_url:
    print(f"Файл оновився: {current_url}")
    # тут — завантажити файл і запустити твою обробку
    file_response = requests.get(current_url)
    with open("latest_mtd.xlsx", "wb") as f:
        f.write(file_response.content)
    save_current_url(current_url)
else:
    print("Оновлень немає")
