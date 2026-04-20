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

# ── Animated emoji (custom_emoji_id from AnimatedEmoji pack) ─────────────────
ANIM = {
    "fire":    ("🔥", "5170202955713872686"),
    "party":   ("🎉", "5170162552956519052"),
    "like":    ("👍", "5172639207193051720"),
    "money":   ("🤑", "5172639606625010326"),
    "robot":   ("🤖", "5172522439917175584"),
    "heart":   ("❤️", "5177198396582139469"),
    "cool":    ("😎", "5168326806624797307"),
    "wow":     ("🤩", "5172506368149553836"),
    "think":   ("🤔", "5170151231422726790"),
    "love":    ("🥰", "5170212941512837033"),
    "evil":    ("😈", "5170215917925171776"),
    "clap":    ("👏", "5170666034792759926"),
    "muscle":  ("💪", "5170288395498291855"),
    "pray":    ("🙏", "5172467013364220537"),
}

def ae(key: str) -> str:
    """Return animated emoji HTML tag."""
    emoji, eid = ANIM[key]
    return f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>'


# ── Prompts ──────────────────────────────────────────────────────────────────
RU_SYSTEM = """Ты — топ-копирайтер магазинов цифровых подписок в Telegram.
Пиши посты точно как у популярных каналов @Heisenbergbest и @crysta1_ressel.

Правила форматирования (строго HTML, без markdown):
- <b>жирный</b> для заголовков и цен
- <i>курсив</i> для дисклеймеров
- Разделители: ━━━━━━━━━━━━━━━━
- Пункты списка: только через эмодзи (🔹 🔸 ✅ 💠)
- Эмодзи кластеры в начале и конце (5-8 шт)
- Цена: зачеркни официальную ~~цена~~ / выдели нашу <b>цена₽</b>
- НИКАКИХ ссылок не придумывай
- Тон: дружелюбный, с характером, энергичный
- Длина: 150-220 слов"""

RU_PROMPTS = {
"promo": """Напиши ПРОДАЮЩИЙ пост для магазина Samec Store на РУССКОМ.

Данные товара:
— Сервис: {name} {emoji}
— Наша цена: {price_ours}₽
— Официальная цена: {price_official}₽
— Описание: {description}

Структура поста:
1. Эмодзи-кластер + <b>НАЗВАНИЕ СЕРВИСА</b>
2. ━━━━━━━━━━━━━━━━
3. Короткий hook — чем крутой этот сервис (2 строки)
4. ━━━━━━━━━━━━━━━━
5. Список фич (3-4 пункта через 🔹)
6. ━━━━━━━━━━━━━━━━
7. 💰 Цена: <s>{price_official}₽</s> → <b>{price_ours}₽</b>  (экономия {economy}₽)
8. ━━━━━━━━━━━━━━━━
9. CTA: для заказа → @samecstore + эмодзи-кластер снизу""",

"deal": """Напиши пост "СДЕЛКА ДНЯ" для Samec Store на РУССКОМ.

Данные:
— Сервис: {name} {emoji}
— Наша цена: {price_ours}₽
— Официальная: {price_official}₽
— Описание: {description}

Структура:
1. 🔥🔥🔥 <b>СДЕЛКА ДНЯ — {name}</b> 🔥🔥🔥
2. ━━━━━━━━━━━━━━━━
3. Hook — почему это огонь (1-2 строки)
4. Что входит (3 пункта через ✅)
5. ━━━━━━━━━━━━━━━━
6. 💥 Было: <s>{price_official}₽</s> | Стало: <b>{price_ours}₽</b>
7. <i>⚡ Мгновенная доставка после оплаты</i>
8. ━━━━━━━━━━━━━━━━
9. 👇 Пиши нам: @samecstore
10. #подписки #{tag}""",

"spotlight": """Напиши пост-обзор "В ЦЕНТРЕ ВНИМАНИЯ" для Samec Store на РУССКОМ.

Данные:
— Сервис: {name} {emoji}
— Наша цена: {price_ours}₽
— Официальная: {price_official}₽
— Описание: {description}

Структура:
1. ✨✨✨ <b>{name} — зачем тебе это?</b>
2. ━━━━━━━━━━━━━━━━
3. 3 неочевидные фичи сервиса (через 🔸)
4. ━━━━━━━━━━━━━━━━
5. Для кого (студенты / фрилансеры / геймеры и т.д.) — 2-3 строки
6. ━━━━━━━━━━━━━━━━
7. 💎 Цена через нас: <b>{price_ours}₽</b> vs официальная <s>{price_official}₽</s>
8. Заказать дешевле 👇 @samecstore
9. #{tag} #самецстор"""
}

EN_PROMPTS = {
"promo": """Write a SELLING post for Samec Store in ENGLISH.

Product:
— Service: {name} {emoji}
— Our price: {price_ours}₽
— Official price: {price_official}₽
— Description: {description}

Structure (HTML only):
1. Emoji cluster + <b>SERVICE NAME</b>
2. ━━━━━━━━━━━━━━━━
3. Short hook — why this rocks (2 lines)
4. ━━━━━━━━━━━━━━━━
5. Features (3-4 points via 🔹)
6. ━━━━━━━━━━━━━━━━
7. 💰 Price: <s>{price_official}₽</s> → <b>{price_ours}₽</b> (save {economy}₽)
8. ━━━━━━━━━━━━━━━━
9. CTA: order now → @samecstore + emoji cluster""",

"deal": """Write a "DEAL OF THE DAY" post for Samec Store in ENGLISH.

Product:
— Service: {name} {emoji}
— Our price: {price_ours}₽
— Official: {price_official}₽
— Description: {description}

Structure:
1. 🔥🔥🔥 <b>DEAL OF THE DAY — {name}</b> 🔥🔥🔥
2. ━━━━━━━━━━━━━━━━
3. Hook — why this is hot (1-2 lines)
4. What's included (3 points via ✅)
5. ━━━━━━━━━━━━━━━━
6. 💥 Was: <s>{price_official}₽</s> | Now: <b>{price_ours}₽</b>
7. <i>⚡ Instant delivery after payment</i>
8. ━━━━━━━━━━━━━━━━
9. 👇 Write us: @samecstore
10. #subscriptions #{tag}""",

"spotlight": """Write a "SPOTLIGHT" review post for Samec Store in ENGLISH.

Product:
— Service: {name} {emoji}
— Our price: {price_ours}₽
— Official: {price_official}₽
— Description: {description}

Structure:
1. ✨✨✨ <b>{name} — why you need it</b>
2. ━━━━━━━━━━━━━━━━
3. 3 underrated features (via 🔸)
4. ━━━━━━━━━━━━━━━━
5. Who it's for (students / freelancers / gamers etc.)
6. ━━━━━━━━━━━━━━━━
7. 💎 Our price: <b>{price_ours}₽</b> vs official <s>{price_official}₽</s>
8. Order cheaper 👇 @samecstore
9. #{tag} #samecstore"""
}


def generate_post(language: str, product: dict, style: str) -> str:
    prompts = RU_PROMPTS if language == "ru" else EN_PROMPTS
    economy = 0
    if product.get("price_official") and product.get("price_ours"):
        economy = product["price_official"] - product["price_ours"]

    prompt = prompts[style].format(
        name=product.get("name", ""),
        emoji=product.get("emoji", ""),
        price_ours=product.get("price_ours", ""),
        price_official=product.get("price_official") or "—",
        description=product.get("description") or "",
        economy=economy,
        tag=product.get("tag", "subscriptions"),
    )

    system = RU_SYSTEM if language == "ru" else RU_SYSTEM.replace("РУССКОМ", "ENGLISH")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.88,
    )
    return response.choices[0].message.content.strip()


def inject_animated_emoji(text: str, style: str) -> str:
    """Replace key static emoji with animated versions in the post."""
    replacements = {
        "🔥": ae("fire"),
        "🎉": ae("party"),
        "🤑": ae("money"),
        "🤩": ae("wow"),
        "💪": ae("muscle"),
        "🙏": ae("pray"),
        "👏": ae("clap"),
    }
    for static, animated in replacements.items():
        text = text.replace(static, animated, 2)
    return text


def get_products_from_db() -> list:
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/products?is_active=eq.true&select=*",
            headers=headers, timeout=10
        )
        resp.raise_for_status()
        products = resp.json()
        if products:
            return products
    except Exception as e:
        print(f"DB error: {e}")
    return [
        {"name": "Spotify Premium", "emoji": "🎵", "tag": "music",
         "price_ours": 149, "price_official": 299, "description": "Музыка без рекламы, офлайн, Hi-Fi"},
        {"name": "Netflix", "emoji": "🎬", "tag": "movie",
         "price_ours": 299, "price_official": 799, "description": "Фильмы и сериалы HD/4K"},
    ]


def get_image(product: dict) -> str | None:
    # 40% chance: generate mascot image with DALL-E
    if random.random() < 0.4:
        from bot.mascot import generate_mascot_image
        print("🎨 Generating mascot image...")
        mascot_url = generate_mascot_image(product)
        if mascot_url:
            print(f"✅ Mascot generated: {mascot_url[:60]}...")
            return mascot_url

    # Use product's uploaded image if available
    if product.get("image_url"):
        return product["image_url"]

    # Fallback: Unsplash photo
    try:
        keywords = {
            "music": "music headphones", "movie": "cinema screen",
            "technology": "artificial intelligence tech", "design": "creative design",
            "gaming": "gaming setup neon", "productivity": "laptop workspace",
            "education": "books learning", "privacy": "cybersecurity",
            "shopping": "online shopping",
        }
        query = keywords.get(product.get("tag", ""), "digital technology").replace(" ", ",")
        resp = requests.get(f"https://source.unsplash.com/1200x630/?{query}",
                            timeout=10, allow_redirects=True)
        if resp.status_code == 200 and "image" in resp.headers.get("content-type", ""):
            return resp.url
    except Exception:
        pass
    return None


def build_keyboard(language: str) -> dict:
    return {"inline_keyboard": [[
        {"text": "🛒 Заказать" if language == "ru" else "🛒 Order now",
         "url": "https://t.me/samecstore"},
        {"text": "💬 Написать" if language == "ru" else "💬 Contact us",
         "url": "https://t.me/samecstore"},
    ]]}


def send_post(text: str, image_url: str | None, keyboard: dict) -> bool:
    if image_url:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            json={"chat_id": TELEGRAM_CHANNEL, "photo": image_url,
                  "caption": text, "parse_mode": "HTML", "reply_markup": keyboard},
            timeout=15
        )
        if resp.status_code == 200:
            return True
        print(f"Photo failed ({resp.status_code}), trying text...")

    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHANNEL, "text": text,
              "parse_mode": "HTML", "reply_markup": keyboard},
        timeout=15
    )
    return resp.status_code == 200


def main():
    products = get_products_from_db()
    product = random.choice(products)
    style = random.choice(["promo", "deal", "spotlight"])

    msk = datetime.now(timezone(timedelta(hours=3)))
    lang = "ru" if msk.hour < 15 else "en"

    print(f"► {product['name']} | {style} | {lang.upper()}")

    text = generate_post(lang, product, style)
    text = inject_animated_emoji(text, style)

    keyboard = build_keyboard(lang)
    image_url = get_image(product)

    success = send_post(text, image_url, keyboard)
    print("✅ Posted!" if success else "❌ Failed")


if __name__ == "__main__":
    main()
