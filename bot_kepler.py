import requests
import time
import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# ===== НАСТРОЙКИ ИЗ ОКРУЖЕНИЯ =====
TOKEN = os.getenv("BOT_TOKEN")
# Превращаем строку из .env "id1,id2" в список Python
RAW_CHATS = os.getenv("CHAT_IDS", "")
CHAT_IDS = [chat.strip() for chat in RAW_CHATS.split(",") if chat.strip()]

if not TOKEN or not CHAT_IDS:
    print("ОШИБКА: Токен или CHAT_IDS не найдены в файле .env")
    exit()

# Остальные настройки
QUERIES = ["lonsdale", "weekend offender", "alpha industries"]
MAX_PRICE = 15
CHECK_INTERVAL = 60 
GBP_TO_KZT = 565

seen_ids = set()
session = requests.Session()

def send_photo(caption, photo_url):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        data = {
            "chat_id": chat_id,
            "caption": caption,
            "photo": photo_url,
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"Ошибка отправки пользователю {chat_id}: {e}")

def get_items(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.vinted.co.uk/"
    }
    if not session.cookies:
        try:
            session.get("https://www.vinted.co.uk/", headers=headers, timeout=10)
        except:
            return {"items": []}

    url = "https://www.vinted.co.uk/api/v2/catalog/items"
    params = {"search_text": query, "order": "newest_first", "per_page": 10, "currency": "GBP"}

    try:
        r = session.get(url, params=params, headers=headers, timeout=10)
        return r.json() if r.status_code == 200 else {"items": []}
    except:
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
    bad_words = ["kids", "fake", "replica", "women", "детск", "девоч"]
    return not any(w in title for w in bad_words)

def format_rating(user):
    try:
        count = user.get("feedback_count", 0)
        if count == 0: return "нет отзывов"
        return f"{user.get('feedback_reputation', 0) * 5:.1f}⭐️ ({count})"
    except:
        return "нет данных"

def check():
    global seen_ids
    for query in QUERIES:
        print(f"Поиск: {query}...")
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
            rating = format_rating(item.get("user", {}))

            text = (
                f"🔥 <b>{title}</b>\n"
                f"💰 <b>{price_gbp} £ (~{price_kzt:,} ₸)</b>\n"
                f"📏 Размер: <b>{size}</b>\n"
                f"⭐️ Продавец: {rating}\n"
                f"🔎 Поиск: {query}\n\n"
                f"{url}"
            ).replace(",", " ")

            if photo:
                send_photo(text, photo)
            else:
                for chat_id in CHAT_IDS:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                 data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
            time.sleep(1)
        time.sleep(2)

print("Бот запущен. Секреты загружены из .env")
while True:
    try:
        check()
        time.sleep(CHECK_INTERVAL)
    except Exception as e:
        print("Ошибка:", e)
        time.sleep(10)