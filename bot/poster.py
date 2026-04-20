import os
import random
import requests
from datetime import date
from openai import OpenAI

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL_ID", "@samecstore")
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

SERVICES = [
    {"name": "Spotify Premium",        "emoji": "🎵", "tag": "music"},
    {"name": "Netflix",                "emoji": "🎬", "tag": "movie"},
    {"name": "YouTube Premium",        "emoji": "▶️",  "tag": "video"},
    {"name": "ChatGPT Plus",           "emoji": "🤖", "tag": "technology"},
    {"name": "Adobe Creative Cloud",   "emoji": "🎨", "tag": "design"},
    {"name": "Canva Pro",              "emoji": "✏️",  "tag": "design"},
    {"name": "Duolingo Plus",          "emoji": "🦉", "tag": "education"},
    {"name": "Apple Music",            "emoji": "🍎", "tag": "music"},
    {"name": "Discord Nitro",          "emoji": "🎮", "tag": "gaming"},
    {"name": "Notion Pro",             "emoji": "📝", "tag": "productivity"},
    {"name": "Figma Pro",              "emoji": "🖌️", "tag": "design"},
    {"name": "Microsoft 365",          "emoji": "💼", "tag": "productivity"},
    {"name": "Amazon Prime",           "emoji": "📦", "tag": "shopping"},
    {"name": "Tidal HiFi",             "emoji": "🎶", "tag": "music"},
    {"name": "NordVPN",                "emoji": "🔒", "tag": "privacy"},
]

POST_STYLES = ["promo", "deal", "spotlight"]

RU_PROMPTS = {
    "promo": """Ты — топ-копирайтер магазина цифровых подписок Samec Store.
Напиши ПРОДАЮЩИЙ пост для Telegram-канала на РУССКОМ языке для сервиса: {service} {emoji}

Структура поста (используй HTML теги):
1. Яркий заголовок с эмодзи (жирный: <b>текст</b>)
2. Короткое описание выгоды (2-3 строки)
3. Цена/скидка (придумай реалистичную скидку 30-60% от официальной)
4. Список преимуществ через эмодзи-буллеты (3-4 пункта)
5. Призыв написать в личку для заказа

Требования:
- Максимум 200 слов
- Много эмодзи уместно по тексту
- Создай ощущение срочности и выгоды
- Упомяни быструю доставку (мгновенно после оплаты)
- НЕ придумывай конкретные ссылки или цены в рублях больше 500р
- Заканчивай: 👇 Пишите нам за подробностями!""",

    "deal": """Ты — копирайтер магазина Samec Store.
Напиши пост "СДЕЛКА ДНЯ" для Telegram на РУССКОМ: {service} {emoji}

Формат (HTML):
1. <b>🔥 СДЕЛКА ДНЯ — {service}</b>
2. Короткий hook (1 предложение почему это круто)
3. Что включено в подписку (3-4 пункта с эмодзи)
4. Акцент на цене — дешевле чем напрямую
5. Ограниченное предложение / таймер давления
6. CTA: написать @samecstore

Тон: энергичный, дружелюбный, без спама""",

    "spotlight": """Ты — копирайтер Samec Store.
Напиши пост "В ЦЕНТРЕ ВНИМАНИЯ" для Telegram на РУССКОМ: {service} {emoji}

Формат (HTML):
1. <b>✨ {service} — зачем это тебе?</b>
2. Расскажи что умеет сервис (неочевидные фичи, 3 пункта)
3. Для кого подходит (студенты / работники / геймеры и т.д.)
4. Цена через нас vs официальная
5. CTA: заказать у нас дешевле 👇

Тон: информативный, как советует друг"""
}

EN_PROMPTS = {
    "promo": """You are a top copywriter for Samec Store — digital subscriptions shop.
Write a SELLING Telegram post in ENGLISH for: {service} {emoji}

Structure (use HTML tags):
1. Catchy headline with emoji (<b>bold</b>)
2. Short benefit description (2-3 lines)
3. Price/discount (realistic 30-60% off official price)
4. Benefits list with emoji bullets (3-4 points)
5. CTA to DM for order

Requirements:
- Max 200 words, energetic tone
- End with: 👇 DM us to order!""",

    "deal": """You are a copywriter for Samec Store.
Write a "DEAL OF THE DAY" Telegram post in ENGLISH: {service} {emoji}

Format (HTML):
1. <b>🔥 DEAL OF THE DAY — {service}</b>
2. Short hook (why this rocks)
3. What's included (3-4 emoji bullet points)
4. Price advantage over official
5. Urgency / limited offer
6. CTA: write to @samecstore""",

    "spotlight": """You are a copywriter for Samec Store.
Write a "SPOTLIGHT" Telegram post in ENGLISH: {service} {emoji}

Format (HTML):
1. <b>✨ {service} — why you need it</b>
2. Hidden/cool features (3 points)
3. Who it's for
4. Our price vs official
5. CTA: get it cheaper with us 👇"""
}


def generate_post(language: str, service: dict, style: str) -> str:
    prompts = RU_PROMPTS if language == "ru" else EN_PROMPTS
    prompt = prompts[style].format(service=service["name"], emoji=service["emoji"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.9,
    )
    return response.choices[0].message.content.strip()


def get_image_url(tag: str) -> str | None:
    try:
        # Unsplash random photo — no API key needed for source.unsplash.com
        keywords = {
            "music": "music headphones",
            "movie": "cinema netflix screen",
            "video": "youtube video content",
            "technology": "artificial intelligence tech",
            "design": "creative design studio",
            "education": "learning education books",
            "gaming": "gaming setup neon",
            "productivity": "productivity workspace laptop",
            "shopping": "online shopping delivery",
            "privacy": "cybersecurity vpn",
        }
        query = keywords.get(tag, "digital technology")
        # Use Unsplash source with 1200x630 (Telegram optimal)
        url = f"https://source.unsplash.com/1200x630/?{query.replace(' ', ',')}"
        resp = requests.get(url, timeout=10, allow_redirects=True)
        if resp.status_code == 200 and "image" in resp.headers.get("content-type", ""):
            return resp.url
    except Exception:
        pass
    return None


def build_keyboard(language: str) -> dict:
    label = "🛒 Заказать подписку" if language == "ru" else "🛒 Order subscription"
    return {
        "inline_keyboard": [[
            {"text": label, "url": "https://t.me/samecstore"},
            {"text": "💬 Написать нам" if language == "ru" else "💬 Contact us",
             "url": "https://t.me/samecstore"},
        ]]
    }


def send_photo_post(text: str, image_url: str, keyboard: dict) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "photo": image_url,
        "caption": text,
        "parse_mode": "HTML",
        "reply_markup": keyboard,
    }
    resp = requests.post(url, json=payload, timeout=15)
    return resp.status_code == 200


def send_text_post(text: str, keyboard: dict) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": keyboard,
        "disable_web_page_preview": False,
    }
    resp = requests.post(url, json=payload, timeout=15)
    return resp.status_code == 200


def main():
    service = random.choice(SERVICES)
    style = random.choice(POST_STYLES)

    # Alternate language by hour: morning RU, evening EN
    from datetime import datetime, timezone, timedelta
    msk = datetime.now(timezone(timedelta(hours=3)))
    lang = "ru" if msk.hour < 15 else "en"

    print(f"Service: {service['name']} | Style: {style} | Lang: {lang.upper()}")

    text = generate_post(lang, service, style)
    print(f"Generated post ({len(text)} chars)")

    keyboard = build_keyboard(lang)
    image_url = get_image_url(service["tag"])

    if image_url:
        print(f"Image: {image_url}")
        success = send_photo_post(text, image_url, keyboard)
        if not success:
            print("Photo failed, falling back to text")
            send_text_post(text, keyboard)
    else:
        send_text_post(text, keyboard)

    print("Posted successfully!")


if __name__ == "__main__":
    main()
