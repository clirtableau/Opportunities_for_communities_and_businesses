import requests
from bs4 import BeautifulSoup

URL = "https://www.kmu.gov.ua/mizhnarodna-tehnichna-dopomoga/perelik-zareiestrovanih-proiektiv-z-planami-zakupivel"
STATE_FILE = "last_known_url.txt"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def get_current_file_url():
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for link in soup.find_all("a", href=True):
        text = link.get_text(strip=True)
        print(f"Знайдено посилання: '{text}' -> {link['href']}")
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
    # тут — завантажити файл і запустити твою обробку
    file_response = requests.get(current_url)
    with open("latest_mtd.xlsx", "wb") as f:
        f.write(file_response.content)
    save_current_url(current_url)
else:
    print("Оновлень немає")
