import os
import random
import requests
from openai import OpenAI

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL_ID", "@samecstore")
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

SERVICES = [
    "Spotify Premium", "Netflix", "YouTube Premium", "ChatGPT Plus",
    "Adobe Creative Cloud", "Canva Pro", "Duolingo Plus", "Apple Music",
    "Discord Nitro", "Notion Pro", "Figma Pro", "Microsoft 365"
]

RU_PROMPT = """Ты — копирайтер магазина цифровых подписок Samec Store (@samecstore).
Напиши короткий продающий пост для Telegram-канала на РУССКОМ языке.

Сервис: {service}

Требования:
- 3-5 предложений максимум
- Начни с цепляющего заголовка с эмодзи
- Упомяни выгоду (цена ниже официальной, мгновенная доставка)
- Призыв к действию: написать в @samecstore_bot
- Используй эмодзи уместно
- Не используй markdown, только текст и эмодзи
- Tone: дружелюбный, энергичный"""

EN_PROMPT = """You are a copywriter for Samec Store (@samecstore) — a digital subscriptions shop.
Write a short selling post for Telegram channel in ENGLISH.

Service: {service}

Requirements:
- Max 3-5 sentences
- Start with a catchy headline with emoji
- Mention the benefit (lower price, instant delivery)
- Call to action: write to @samecstore_bot
- Use emojis naturally
- No markdown, just text and emojis
- Tone: friendly, energetic"""

def generate_post(language: str, service: str) -> str:
    prompt = RU_PROMPT if language == "ru" else EN_PROMPT
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt.format(service=service)}],
        max_tokens=300,
        temperature=0.85,
    )
    return response.choices[0].message.content.strip()

def post_to_telegram(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": text,
        "parse_mode": "",
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    return True

def main():
    service = random.choice(SERVICES)
    # Alternate languages: odd days RU, even days EN
    from datetime import date
    lang = "ru" if date.today().day % 2 != 0 else "en"

    print(f"Generating {lang.upper()} post for: {service}")
    text = generate_post(lang, service)
    print(f"Post:\n{text}\n")
    post_to_telegram(text)
    print("Posted successfully!")

if __name__ == "__main__":
    main()
