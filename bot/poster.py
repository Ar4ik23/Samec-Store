import os
import json
import random
import requests
from datetime import datetime, timezone, timedelta
from openai import OpenAI

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL_ID", "@samecstore")
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# ── Animated emoji ────────────────────────────────────────────────────────────
ANIM = {
    "fire":   ("🔥", "5170202955713872686"),
    "party":  ("🎉", "5170162552956519052"),
    "money":  ("🤑", "5172639606625010326"),
    "wow":    ("🤩", "5172506368149553836"),
    "muscle": ("💪", "5170288395498291855"),
    "pray":   ("🙏", "5172467013364220537"),
    "clap":   ("👏", "5170666034792759926"),
}

def ae(key):
    emoji, eid = ANIM[key]
    return f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>'


# ── Load products from file ───────────────────────────────────────────────────
def get_products():
    try:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "products.json")
        with open(path, encoding="utf-8") as f:
            all_products = json.load(f)
        active = [p for p in all_products if p.get("active", True)]
        return active if active else all_products
    except Exception as e:
        print(f"products.json error: {e}")
        return []


# ── Prompts ───────────────────────────────────────────────────────────────────
SYSTEM_RU = """Ты — топ-копирайтер магазина цифровых подписок Samec Store.
Пиши как в популярных Telegram-каналах @Heisenbergbest и @crysta1_ressel.

Только HTML теги: <b>жирный</b>, <i>курсив</i>, <s>зачёркнутый</s>
Разделители: ━━━━━━━━━━━━━━━━
Пункты: через эмодзи (🔹 ✅ 🔸)
Тон: дружелюбный, энергичный, с характером. 150-220 слов."""

PROMPTS_RU = {
"promo": """Продающий пост для: {name} {emoji}
Наша цена: {price_ours}₽ | Официальная: {price_official}₽
Описание: {description}

Структура:
1. Эмодзи-кластер + <b>{name}</b>
2. ━━━━━━━━━━━━━━━━
3. Hook — почему это must-have (2 строки)
4. ━━━━━━━━━━━━━━━━
5. Фичи (3-4 пункта через 🔹)
6. ━━━━━━━━━━━━━━━━
7. 💰 <s>{price_official}₽</s> → <b>{price_ours}₽</b> (экономия {economy}₽)
8. ━━━━━━━━━━━━━━━━
9. 👇 Заказать: @samecstore""",

"deal": """Пост СДЕЛКА ДНЯ для: {name} {emoji}
Наша цена: {price_ours}₽ | Официальная: {price_official}₽
Описание: {description}

Структура:
1. 🔥🔥🔥 <b>СДЕЛКА ДНЯ — {name}</b> 🔥🔥🔥
2. ━━━━━━━━━━━━━━━━
3. Hook (1-2 строки)
4. Что входит (3 пункта ✅)
5. ━━━━━━━━━━━━━━━━
6. 💥 Было: <s>{price_official}₽</s> | Стало: <b>{price_ours}₽</b>
7. <i>⚡ Мгновенная доставка после оплаты</i>
8. ━━━━━━━━━━━━━━━━
9. 👇 @samecstore | #{tag}""",

"spotlight": """Пост ОБЗОР для: {name} {emoji}
Наша цена: {price_ours}₽ | Официальная: {price_official}₽
Описание: {description}

Структура:
1. ✨✨✨ <b>{name} — зачем тебе это?</b>
2. ━━━━━━━━━━━━━━━━
3. 3 неочевидные фичи (через 🔸)
4. ━━━━━━━━━━━━━━━━
5. Для кого подходит (2-3 строки)
6. ━━━━━━━━━━━━━━━━
7. 💎 Наша цена: <b>{price_ours}₽</b> vs <s>{price_official}₽</s>
8. 👇 @samecstore | #{tag}"""
}

SYSTEM_EN = "You are a top copywriter for Samec Store digital subscriptions shop. Write like popular Telegram store channels. HTML only: <b>bold</b>, <i>italic</i>, <s>strike</s>. Separators: ━━━━━━━━━━━━━━━━. Bullets via emoji. Friendly, energetic tone. 150-220 words."

PROMPTS_EN = {
"promo": """Selling post for: {name} {emoji}
Our price: {price_ours}₽ | Official: {price_official}₽
Description: {description}

Structure:
1. Emoji cluster + <b>{name}</b>
2. ━━━━━━━━━━━━━━━━
3. Hook — why this is must-have
4. ━━━━━━━━━━━━━━━━
5. Features (3-4 via 🔹)
6. ━━━━━━━━━━━━━━━━
7. 💰 <s>{price_official}₽</s> → <b>{price_ours}₽</b> (save {economy}₽)
8. ━━━━━━━━━━━━━━━━
9. 👇 Order: @samecstore""",

"deal": """DEAL OF THE DAY post for: {name} {emoji}
Our price: {price_ours}₽ | Official: {price_official}₽
Description: {description}

Structure:
1. 🔥🔥🔥 <b>DEAL OF THE DAY — {name}</b> 🔥🔥🔥
2. ━━━━━━━━━━━━━━━━
3. Hook (1-2 lines)
4. What's included (3 via ✅)
5. ━━━━━━━━━━━━━━━━
6. 💥 Was: <s>{price_official}₽</s> | Now: <b>{price_ours}₽</b>
7. <i>⚡ Instant delivery after payment</i>
8. ━━━━━━━━━━━━━━━━
9. 👇 @samecstore | #{tag}""",

"spotlight": """SPOTLIGHT post for: {name} {emoji}
Our price: {price_ours}₽ | Official: {price_official}₽
Description: {description}

Structure:
1. ✨✨✨ <b>{name} — why you need it</b>
2. ━━━━━━━━━━━━━━━━
3. 3 underrated features (via 🔸)
4. ━━━━━━━━━━━━━━━━
5. Who it's for (2-3 lines)
6. ━━━━━━━━━━━━━━━━
7. 💎 Our price: <b>{price_ours}₽</b> vs <s>{price_official}₽</s>
8. 👇 @samecstore | #{tag}"""
}


def generate_post(lang, product, style):
    economy = (product.get("price_official") or 0) - (product.get("price_ours") or 0)
    prompts = PROMPTS_RU if lang == "ru" else PROMPTS_EN
    system = SYSTEM_RU if lang == "ru" else SYSTEM_EN
    prompt = prompts[style].format(
        name=product.get("name", ""),
        emoji=product.get("emoji", ""),
        price_ours=product.get("price_ours", ""),
        price_official=product.get("price_official") or "—",
        description=product.get("description") or "",
        economy=max(economy, 0),
        tag=product.get("tag", "subscriptions"),
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        max_tokens=500, temperature=0.88,
    )
    return resp.choices[0].message.content.strip()


def inject_animated_emoji(text):
    for static, (_, eid) in ANIM.items():
        emoji = {"fire":"🔥","party":"🎉","money":"🤑","wow":"🤩","muscle":"💪","pray":"🙏","clap":"👏"}[static]
        text = text.replace(emoji, f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>', 2)
    return text


def get_image(product):
    from bot.mascot import generate_mascot_image
    if random.random() < 0.4:
        url = generate_mascot_image(product)
        if url:
            return url
    if product.get("image_url"):
        return product["image_url"]
    try:
        keywords = {
            "music": "music headphones", "movie": "cinema screen",
            "technology": "artificial intelligence tech", "design": "creative design",
            "gaming": "gaming setup neon", "productivity": "laptop workspace",
            "education": "books learning", "privacy": "cybersecurity", "shopping": "online shopping",
        }
        q = keywords.get(product.get("tag", ""), "digital technology").replace(" ", ",")
        r = requests.get(f"https://source.unsplash.com/1200x630/?{q}", timeout=10, allow_redirects=True)
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            return r.url
    except Exception:
        pass
    return None


def build_keyboard(lang):
    return {"inline_keyboard": [[
        {"text": "🛒 Заказать" if lang == "ru" else "🛒 Order", "url": "https://t.me/samecstore"},
        {"text": "💬 Написать" if lang == "ru" else "💬 Contact", "url": "https://t.me/samecstore"},
    ]]}


def send_post(text, image_url, keyboard):
    if image_url:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", json={
            "chat_id": TELEGRAM_CHANNEL, "photo": image_url,
            "caption": text, "parse_mode": "HTML", "reply_markup": keyboard,
        }, timeout=15)
        if r.status_code == 200:
            return True
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={
        "chat_id": TELEGRAM_CHANNEL, "text": text,
        "parse_mode": "HTML", "reply_markup": keyboard,
    }, timeout=15)
    return r.status_code == 200


def main():
    products = get_products()
    if not products:
        print("No products in products.json!")
        return

    product = random.choice(products)
    style = random.choice(["promo", "deal", "spotlight"])
    msk = datetime.now(timezone(timedelta(hours=3)))
    lang = "ru" if msk.hour < 15 else "en"

    print(f"Posting: {product['name']} | {style} | {lang.upper()}")
    text = generate_post(lang, product, style)
    text = inject_animated_emoji(text)
    success = send_post(text, get_image(product), build_keyboard(lang))
    print("OK" if success else "FAILED")


if __name__ == "__main__":
    main()
