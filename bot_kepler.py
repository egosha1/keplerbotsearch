import requests
import time
import os
from dotenv import load_dotenv

# Загружаем переменные
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
RAW_CHATS = os.getenv("CHAT_IDS", "")
CHAT_IDS = [chat.strip() for chat in RAW_CHATS.split(",") if chat.strip()]

if not TOKEN or not CHAT_IDS:
    print("ОШИБКА: Токен или CHAT_IDS не найдены")
    exit()

# Настройки
QUERIES = ["lonsdale", "weekend offender", "alpha industries"]
MAX_PRICE = 15
CHECK_INTERVAL = 60 
GBP_TO_KZT = 565

seen_ids = set()
# Создаем глобальную сессию
session = requests.Session()
iteration_count = 0

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": "https://www.vinted.co.uk/",
        "Origin": "https://www.vinted.co.uk"
    }

def refresh_session():
    """Сброс сессии для обхода блокировок по кукам"""
    global session
    print("--- Обновление сессии и кук ---")
    session = requests.Session()
    try:
        session.get("https://www.vinted.co.uk/", headers=get_headers(), timeout=15)
    except:
        pass

def get_items(query):
    url = "https://www.vinted.co.uk/api/v2/catalog/items"
    params = {"search_text": query, "order": "newest_first", "per_page": 15, "currency": "GBP"}
    
    try:
        r = session.get(url, params=params, headers=get_headers(), timeout=15)
        # Если получаем 403 или 401, пробуем обновить куки один раз
        if r.status_code in [401, 403]:
            refresh_session()
            r = session.get(url, params=params, headers=get_headers(), timeout=15)
            
        print(f"Поиск {query}: Статус {r.status_code}")
        return r.json() if r.status_code == 200 else {"items": []}
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return {"items": []}

def extract_price(item):
    try:
        raw_price = item.get("price")
        if isinstance(raw_price, dict):
            return float(raw_price.get("amount", 0))
        return float(str(raw_price).replace(",", "."))
    except:
        return 0.0

def is_good(item, price):
    if price > MAX_PRICE or price <= 0:
        return False
    title = item.get("title", "").lower()
    bad_words = ["kids", "fake", "replica", "детск", "девоч", "girl", "boy", "book"]
    return not any(w in title for w in bad_words)

def check():
    global seen_ids, iteration_count
    
    # Каждые 10 кругов обновляем сессию полностью
    iteration_count += 1
    if iteration_count % 10 == 0:
        refresh_session()

    for query in QUERIES:
        data = get_items(query)

        for item in data.get("items", []):
            item_id = item["id"]
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            price_gbp = extract_price(item)
            if not is_good(item, price_gbp):
                continue

            price_kzt = int(price_gbp * GBP_TO_KZT)
            size = item.get("size_title", "Не указан")
            title = item.get("title", "Без названия")
            url = item.get("url", "")
            photo = item.get("photo", {}).get("url") if item.get("photo") else None
            
            # Собираем текст
            text = (
                f"🔥 <b>{title}</b>\n"
                f"💰 <b>{price_gbp} £ (~{price_kzt:,} ₸)</b>\n"
                f"📏 Размер: <b>{size}</b>\n"
                f"🔎 Поиск: {query}\n\n"
                f"{url}"
            )

            # Отправка
            for chat_id in CHAT_IDS:
                try:
                    if photo:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                     data={"chat_id": chat_id, "caption": text, "photo": photo, "parse_mode": "HTML"}, timeout=10)
                    else:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                     data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
                except:
                    pass
            time.sleep(1) # Пауза между отправками, чтобы ТГ не забанил
        time.sleep(2) # Пауза между брендами

# СТАРТ
if __name__ == "__main__":
    print("=== БОТ ЗАПУЩЕН НА RAILWAY 24/7 ===")
    refresh_session() # Начальная инициализация кук
    while True:
        try:
            check()
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            time.sleep(20)
