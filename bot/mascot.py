import os
import random
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

MASCOT_BASE = (
    "A cartoon capybara mascot: orange-brown fur, STRIKING BLUE EYES, large rounded nose, "
    "confident smug expression. OUTFIT: white puffer jacket open, black hoodie inside, "
    "teal mint-green jogger pants, white and blue sneakers, silver chain necklace. "
    "Stocky cute body. Vibrant cartoon illustration style, clean bold lines, white background. "
    "SAME character design every time — brand mascot consistency."
)

SCENES = {
    "music": [
        "wearing large DJ headphones, in neon music studio with mixing board, vinyl record in hand, musical notes floating",
        "on stage at concert with spotlight, microphone in hand, colorful stage lights",
        "chilling with wireless earbuds, floating music equalizer bars and notes around",
    ],
    "movie": [
        "on couch with popcorn bucket, wearing 3D glasses, huge movie screen behind, TV remote in hand",
        "in home cinema setup, reclining chair, floating Netflix/play button icons around",
        "dressed as movie director with clapperboard, film reel background",
    ],
    "technology": [
        "at futuristic holographic computer, multiple floating screens with AI visuals and code, glowing blue light",
        "with AI hologram next to it, typing on glowing keyboard, digital brain visualization floating",
        "wearing VR headset, surrounded by digital data streams and neural network patterns",
    ],
    "design": [
        "in artist studio with canvases, holding paint palette and brush, colorful paint splashes",
        "at professional design workstation with dual monitors, stylus in hand",
        "wearing beret, surrounded by floating design elements — shapes, colors, typography",
    ],
    "gaming": [
        "in gaming chair with RGB setup, holding controller, neon lights and game icons around",
        "wearing gaming headset, multiple screens showing games, energy drink on desk",
        "in gamer hoodie with controller, pixelated game elements and achievement badges floating",
    ],
    "productivity": [
        "at clean modern desk with laptop, coffee cup, floating task and calendar icons",
        "holding tablet with charts, business-like pose, floating productivity app icons",
    ],
    "education": [
        "wearing graduation cap over puffer jacket, diploma in hand, floating books and language flags",
        "at study desk with books stacked, globe nearby, excited learning expression",
    ],
    "privacy": [
        "surrounded by lock icons and shield symbols, dark mysterious vibe, padlock in hand",
        "with superhero VPN shield, cape added over puffer jacket, cyber protection theme",
    ],
    "shopping": [
        "holding multiple shopping bags, delivery box at feet, discount price tags floating",
        "pushing cart full of digital subscription boxes, happy expression",
    ],
}

DEFAULT_SCENES = [
    "standing confidently arms crossed, colorful digital app icons floating around (Spotify, Netflix, YouTube)",
    "giving thumbs up, discount signs and gold coins floating around, happy expression",
    "holding smartphone showing a subscription app, glowing deals and offers around",
]


def generate_mascot_image(product: dict) -> str | None:
    tag = product.get("tag", "technology")
    scenes = SCENES.get(tag, DEFAULT_SCENES)
    scene = random.choice(scenes)

    prompt = (
        f"{MASCOT_BASE} "
        f"Scene: {scene}. "
        f"Promoting {product.get('name', 'digital subscription')}. "
        f"High quality cartoon illustration, bright engaging colors. No text in image."
    )

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        print(f"Mascot gen failed: {e}")
        return None
