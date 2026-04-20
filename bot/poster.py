import os
import random
import requests
from datetime import datetime, timezone, timedelta
from openai import OpenAI

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL_ID", "@samecstore")
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_ANON_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

RU_PROMPTS = {
    "promo": """Ты — топ-копирайтер магазина цифровых подписок Samec Store.
Напиши ПРОДАЮЩИЙ пост для Telegram-канала на РУССКОМ языке.

Сервис: {name} {emoji}
Наша цена: {price_ours}₽
Официальная цена: {price_official}
Описание: {description}

Структура (HTML теги):
1. Яркий заголовок с эмодзи (<b>жирный</b>)
2. Короткое описание выгоды (2-3 строки)
3. Преимущества через эмодзи-буллеты (3-4 пункта)
4. Цена: наша vs официальная, % скидки
5. Конец: 👇 Пишите нам за подробностями!

Максимум 200 слов. Тон: энергичный, дружелюбный.""",

    "deal": """Ты — копирайтер Samec Store. Напиши пост "СДЕЛКА ДНЯ" на РУССКОМ.

Сервис: {name} {emoji}
Наша цена: {price_ours}₽
Официальная цена: {price_official}
Описание: {description}

Формат (HTML):
1. <b>🔥 СДЕЛКА ДНЯ — {name}</b>
2. Короткий hook (1 предложение)
3. Что включено (3-4 пункта с эмодзи)
4. Цена — выгода vs официальная
5. Ограниченное предложение
6. CTA: написать @samecstore""",

    "spotlight": """Ты — копирайтер Samec Store. Напиши пост "В ЦЕНТРЕ ВНИМАНИЯ" на РУССКОМ.

Сервис: {name} {emoji}
Наша цена: {price_ours}₽
Описание: {description}

Формат (HTML):
1. <b>✨ {name} — зачем это тебе?</b>
2. Неочевидные фичи сервиса (3 пункта)
3. Для кого подходит
4. Цена через нас vs официальная
5. CTA: заказать дешевле 👇"""
}

EN_PROMPTS = {
    "promo": """You are a copywriter for Samec Store. Write a SELLING Telegram post in ENGLISH.

Service: {name} {emoji}
Our price: {price_ours}₽
Official price: {price_official}
Description: {description}

Structure (HTML tags):
1. Catchy headline with emoji (<b>bold</b>)
2. Short benefit description
3. Benefits list with emoji (3-4 points)
4. Price: ours vs official, % discount
5. End: 👇 DM us to order!

Max 200 words. Tone: energetic, friendly.""",

    "deal": """You are a copywriter for Samec Store. Write a "DEAL OF THE DAY" post in ENGLISH.

Service: {name} {emoji}
Our price: {price_ours}₽
Official price: {price_official}
Description: {description}

Format (HTML):
1. <b>🔥 DEAL OF THE DAY — {name}</b>
2. Short hook
3. What's included (3-4 emoji points)
4. Price advantage
5. Urgency / limited offer
6. CTA: write to @samecstore""",

    "spotlight": """You are a copywriter for Samec Store. Write a "SPOTLIGHT" post in ENGLISH.

Service: {name} {emoji}
Our price: {price_ours}₽
Description: {description}

Format (HTML):
1. <b>✨ {name} — why you need it</b>
2. Cool/hidden features (3 points)
3. Who it's for
4. Our price vs official
5. CTA: get it cheaper with us 👇"""
}

FALLBACK_SERVICES = [
    {"name": "Spotify Premium", "emoji": "🎵", "tag": "music", "price_ours": 149, "price_official": 299, "description": "Музыка без рекламы, офлайн режим, Hi-Fi качество"},
    {"name": "Netflix", "emoji": "🎬", "tag": "movie", "price_ours": 299, "price_official": 799, "description": "Фильмы и сериалы в HD/4K без рекламы"},
    {"name": "ChatGPT Plus", "emoji": "🤖", "tag": "technology", "price_ours": 799, "price_official": 1800, "description": "GPT-4o, генерация изображений, приоритетный доступ"},
]


def get_products_from_db() -> list:
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        url = f"{SUPABASE_URL}/rest/v1/products?is_active=eq.true&select=*"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        products = resp.json()
        if products:
            return products
    except Exception as e:
        print(f"DB error: {e}, using fallback")
    return FALLBACK_SERVICES


def generate_post(language: str, product: dict, style: str) -> str:
    prompts = RU_PROMPTS if language == "ru" else EN_PROMPTS
    prompt = prompts[style].format(
        name=product.get("name", ""),
        emoji=product.get("emoji", ""),
        price_ours=product.get("price_ours", ""),
        price_official=product.get("price_official") or "нет данных",
        description=product.get("description") or "",
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.9,
    )
    return response.choices[0].message.content.strip()


def get_fallback_image(tag: str) -> str | None:
    try:
        keywords = {
            "music": "music headphones", "movie": "cinema screen",
            "technology": "artificial intelligence", "design": "creative studio",
            "gaming": "gaming setup neon", "productivity": "workspace laptop",
            "education": "learning books", "privacy": "cybersecurity",
            "shopping": "online shopping",
        }
        query = keywords.get(tag or "technology", "digital technology").replace(" ", ",")
        resp = requests.get(f"https://source.unsplash.com/1200x630/?{query}", timeout=10, allow_redirects=True)
        if resp.status_code == 200 and "image" in resp.headers.get("content-type", ""):
            return resp.url
    except Exception:
        pass
    return None


def build_keyboard(language: str) -> dict:
    return {
        "inline_keyboard": [[
            {"text": "🛒 Заказать" if language == "ru" else "🛒 Order", "url": "https://t.me/samecstore"},
            {"text": "💬 Написать" if language == "ru" else "💬 Contact", "url": "https://t.me/samecstore"},
        ]]
    }


def send_photo_post(text: str, image_url: str, keyboard: dict) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHANNEL, "photo": image_url,
        "caption": text, "parse_mode": "HTML", "reply_markup": keyboard,
    }, timeout=15)
    return resp.status_code == 200


def send_text_post(text: str, keyboard: dict) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHANNEL, "text": text,
        "parse_mode": "HTML", "reply_markup": keyboard,
    }, timeout=15)
    return resp.status_code == 200


def main():
    products = get_products_from_db()
    product = random.choice(products)
    style = random.choice(["promo", "deal", "spotlight"])

    msk = datetime.now(timezone(timedelta(hours=3)))
    lang = "ru" if msk.hour < 15 else "en"

    print(f"Product: {product['name']} | Style: {style} | Lang: {lang.upper()}")

    text = generate_post(lang, product, style)
    keyboard = build_keyboard(lang)

    image_url = product.get("image_url") or get_fallback_image(product.get("tag"))

    if image_url:
        success = send_photo_post(text, image_url, keyboard)
        if not success:
            send_text_post(text, keyboard)
    else:
        send_text_post(text, keyboard)

    print("Posted successfully!")


if __name__ == "__main__":
    main()
