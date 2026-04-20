import os
import requests
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_ANON_KEY"]

# Core character description — always included in every generation prompt
MASCOT_REFERENCE_URL = "https://pfijhdzwjyrypmnwojvn.supabase.co/storage/v1/object/public/product-images/mascot_reference.png"

MASCOT_BASE = (
    "A cartoon capybara mascot character — EXACT SAME DESIGN as the Samec Store brand mascot: "
    "orange-brown fur, STRIKING BLUE EYES (very important), large rounded capybara nose, "
    "confident slightly smug expression, chubby cheeks. "
    "OUTFIT (must match exactly): white puffer jacket open, black hoodie/t-shirt inside, "
    "teal mint-green jogger pants, white and blue Nike-style sneakers, silver chain necklace around neck. "
    "Stocky cute body proportions, short legs. "
    "Style: vibrant cartoon illustration, clean bold lines, bright colors, "
    "white or simple background. Character must look like the SAME mascot every time."
)

# Product-specific scenes — costume + context per category
SCENES = {
    "music": [
        "wearing large DJ headphones around neck, standing in a neon-lit music studio with mixing board, holding vinyl record, musical notes floating around",
        "on stage at a concert with spotlight, microphone in hand, crowd cheering, colorful stage lights",
        "relaxing with wireless earbuds in, surrounded by floating music notes and equalizer bars",
    ],
    "movie": [
        "sitting on a couch with popcorn bucket, wearing 3D glasses, huge screen showing movies behind, TV remote in hand",
        "in a home cinema setup, reclining chair, surrounded by floating movie icons (Netflix, play buttons)",
        "dressed as a movie director with clapperboard, film reel background, director's chair",
    ],
    "technology": [
        "sitting at a futuristic holographic computer setup, multiple floating screens with code and AI visuals, glowing blue light",
        "with a robot arm/AI hologram next to it, typing on a glowing keyboard, digital brain visualization",
        "wearing a VR headset, surrounded by digital data streams and neural network patterns",
    ],
    "design": [
        "in an artist studio surrounded by canvases, holding a paint palette and brush, colorful paint splashes around",
        "at a professional design workstation with dual monitors showing creative work, stylus in hand",
        "wearing a beret, surrounded by floating design elements (shapes, colors, typography)",
    ],
    "gaming": [
        "in a gaming chair with RGB setup, holding game controller, surrounded by floating game icons and neon lights",
        "wearing a gaming headset, multiple screens showing games, energy drink on desk",
        "in a gamer hoodie with controller, pixelated game elements and achievement badges floating around",
    ],
    "productivity": [
        "at a clean modern office desk with laptop, coffee cup, plants, organized workspace with floating task icons",
        "holding a tablet with charts and notes, business casual outfit added over the jacket, confident pose",
        "surrounded by floating calendar, checklist, and productivity app icons, focused expression",
    ],
    "education": [
        "wearing graduation cap over the puffer jacket, holding diploma, surrounded by floating books and languages",
        "at a study desk with books stacked, globe nearby, language flags floating, studious expression",
        "holding a language app phone, flags of different countries floating, excited learning expression",
    ],
    "privacy": [
        "wearing a dark hoodie pulled up, surrounded by lock icons and shield symbols, mysterious pose",
        "standing in front of a globe with a VPN shield, cyber security icons, padlock in hand",
        "with a superhero-style shield with a lock symbol, cape added, cyber protection theme",
    ],
    "shopping": [
        "holding multiple shopping bags, delivery box at feet, online shopping icons floating around, happy expression",
        "pushing a shopping cart full of digital subscription boxes, price tags with discounts visible",
        "surrounded by Amazon-style delivery boxes and packages, one package open with light coming out",
    ],
}

DEFAULT_SCENE = [
    "standing confidently with arms crossed, colorful digital subscription app icons floating around (Spotify, Netflix, YouTube logos)",
    "giving thumbs up, surrounded by discount percentage signs and price tags, gold coins floating",
    "holding a smartphone showing a digital subscription, glowing deals and offers around",
]


def get_scene(tag: str) -> str:
    import random
    scenes = SCENES.get(tag, DEFAULT_SCENE)
    return random.choice(scenes)


def generate_mascot_image(product: dict) -> str | None:
    """Generate a mascot image for the product and return URL."""
    tag = product.get("tag", "technology")
    scene = get_scene(tag)
    service_name = product.get("name", "")

    prompt = (
        f"{MASCOT_BASE} "
        f"Scene: {scene}. "
        f"Context: promoting {service_name} digital subscription. "
        f"High quality cartoon illustration, bright and engaging, suitable for a Telegram store channel post. "
        f"No text in the image."
    )

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url

        # Download and upload to Supabase for permanent storage
        img_data = requests.get(image_url, timeout=30).content
        filename = f"mascot_{product.get('tag', 'default')}_{__import__('time').time_ns()}.png"

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "image/png",
        }
        upload_resp = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/product-images/{filename}",
            headers=headers,
            data=img_data,
            timeout=30,
        )

        if upload_resp.status_code in (200, 201):
            return f"{SUPABASE_URL}/storage/v1/object/public/product-images/{filename}"
        else:
            return image_url  # fallback: use temporary DALL-E URL
    except Exception as e:
        print(f"Mascot generation failed: {e}")
        return None
