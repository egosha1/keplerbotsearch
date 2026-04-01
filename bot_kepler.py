import requests
import time
import os
from dotenv import load_dotenv

# Принудительно загружаем переменные
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
RAW_CHATS = os.getenv("CHAT_IDS", "")
CHAT_IDS = [c.strip() for c in RAW_CHATS.split(",") if c.strip()]

# Если данных нет, пишем в логи и выходим, чтобы не гадать
if not TOKEN or not CHAT_IDS:
    print(f"!!! КРИТИЧЕСКАЯ ОШИБКА: TOKEN={TOKEN}, CHATS={CHAT_IDS}")
    exit(1)

def check_vinted():
    print("--> Начинаю обход запросов...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": "https://www.vinted.co.uk/"
    }
    
    # Пытаемся получить куки один раз
    try:
        s = requests.Session()
        s.get("https://www.vinted.co.uk/", headers=headers, timeout=10)
        
        # Проверяем только одну категорию для теста
        url = "https://www.vinted.co.uk/api/v2/catalog/items"
        params = {"search_text": "lonsdale", "order": "newest_first", "per_page": 5}
        
        res = s.get(url, params=params, headers=headers, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            items = data.get("items", [])
            print(f"Успех! Найдено {len(items)} товаров.")
            # Тут логика отправки (как в прошлых версиях)
        else:
            print(f"Vinted ответил кодом {res.status_code} (возможен бан IP хостинга)")
            
    except Exception as e:
        print(f"Ошибка при запросе: {e}")

if __name__ == "__main__":
    print("=== БОТ ОЖИЛ И СТАРТОВАЛ ===")
    while True:
        try:
            check_vinted()
        except Exception as e:
            print(f"Ошибка в цикле: {e}")
        time.sleep(60)