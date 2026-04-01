import requests
import time
import os
from dotenv import load_dotenv

# Загружаем секреты
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
RAW_CHATS = os.getenv("CHAT_IDS", "")
CHAT_IDS = [chat.strip() for chat in RAW_CHATS.split(",") if chat.strip()]

# Константы
QUERIES = ["lonsdale", "weekend offender", "alpha industries"]
MAX_PRICE = 15
CHECK_INTERVAL = 60 
GBP_TO_KZT = 565

seen_ids = set()
session = requests.Session()

def get_items(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.vinted.co.uk/"
    }
    try:
        if not session.cookies:
            session.get("https://www.vinted.co.uk/", headers=headers, timeout=10)
        
        url = "https://www.vinted.co.uk/api/v2/catalog/items"
        params = {"search_text": query, "order": "newest_first", "per_page": 10, "currency": "GBP"}
        
        r = session.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
        print(f"(!) Ошибка Vinted: {r.status_code}")
        return {"items": []}
    except Exception as e:
        print(f"(!) Ошибка сети: {e}")
        return {"items": []}

def check():
    global seen_ids
    for query in QUERIES:
        print(f"--> Проверка категории: {query}")
        data = get_items(query)
        items = data.get("items", [])
        print(f"Найдено товаров: {len(items)}")

        for item in items:
            item_id = item["id"]
            if item_id in seen_ids: continue
            seen_ids.add(item_id)

            # Извлекаем цену
            raw_price = item.get("price")
            price_gbp = float(raw_price.get("amount", 0)) if isinstance(raw_price, dict) else float(str(raw_price or 0).replace(",", "."))
            
            # Фильтр
            if price_gbp > MAX_PRICE or price_gbp <= 0: continue
            title = item.get("title", "").lower()
            if any(w in title for w in ["kids", "fake", "replica", "women", "детск"]): continue

            # Данные
            price_kzt = int(price_gbp * GBP_TO_KZT)
            size = item.get("size_title", "Не указан")
            url = item.get("url", "")
            
            text = (f"🔥 <b>{item.get('title')}</b>\n"
                    f"💰 <b>{price_gbp} £ (~{price_kzt:,} ₸)</b>\n"
                    f"📏 Размер: <b>{size}</b>\n"
                    f"🔎 Поиск: {query}\n\n{url}").replace(",", " ")

            # Отправка всем
            for chat_id in CHAT_IDS:
                img = item.get("photo", {}).get("url")
                if img:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={"chat_id": chat_id, "caption": text, "photo": img, "parse_mode": "HTML"})
                else:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        time.sleep(2)

# ГЛАВНЫЙ ЗАПУСК
if __name__ == "__main__":
    print("=== БОТ СТАРТОВАЛ ===")
    print(f"Загружено чатов: {len(CHAT_IDS)}")
    
    while True:
        try:
            check()
            print(f"Спим {CHECK_INTERVAL} сек...")
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            time.sleep(20)