from flask import Flask, render_template, request, jsonify, session
import requests
import json
import re
import random
import urllib.parse
from emotion_engine import PlayerEmotionEngine

app = Flask(__name__)
import os
import base64

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.secret_key = os.environ.get("SECRET_KEY", "dungeon-master-secret-x7k2")
emotion_engine = PlayerEmotionEngine()

# ── LLM Configuration ───────────────────────────────────────────────────────
OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL        = os.environ.get("MODEL", "llama3.2")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

REQUIRED_KEYS = ["story", "choices", "hp", "max_hp", "inventory",
                 "emotion", "game_over", "victory"]

SYSTEM_PROMPT = """You are an immersive, emotion-aware AI Dungeon Master running a text-based RPG.

CRITICAL: Respond with ONLY raw valid JSON. No markdown. No code blocks. No explanation. Just the JSON object.

Always use EXACTLY this structure:
{
  "story": "2-4 sentence vivid narrative of what happens",
  "image_prompt": "cinematic scene description under 20 words",
  "choices": ["Action choice A", "Action choice B", "Action choice C"],
  "hp": 100,
  "max_hp": 100,
  "inventory": [],
  "emotion": "calm",
  "game_over": false,
  "victory": false,
  "death_message": "",
  "victory_message": ""
}

emotion field must be exactly one of: calm, tense, fearful, excited, triumphant, grieving, enraged

STORYTELLING — match your prose to the emotion:
- calm: peaceful, descriptive, world-building
- tense: short choppy sentences, rising dread
- fearful: sensory overload, panic, uncertainty
- excited: fast-paced, kinetic, vivid action
- triumphant: epic, soaring, heroic language
- grieving: slow, mournful, poetic
- enraged: visceral, raw, explosive

GAME RULES:
- HP starts at 100. Danger = subtract 10-30. Healing = add 5-15.
- Add items to inventory when player finds them; remove when used.
- Set game_over to true and fill death_message when HP reaches 0.
- Set victory to true and fill victory_message when quest completes.
- Always give exactly 3 distinct meaningful choices.
- Reference past events and inventory items in the story.
- image_prompt must be vivid and under 20 words.
"""

# ── Adaptive Procedural Engine (Guaranteed 100% uptime on Render/Cloud) ──────
GENRE_BEATS = {
    "fantasy": {
        "intro": "The ancient bell of Eldoria tolls as dusk falls. In the ruins of the Sunken Citadel, a glowing sigil flares to life beneath your feet, humming with forbidden sorcery.",
        "image": "ancient fantasy ruins glowing arcane runes atmospheric misty twilight",
        "items": ["Runestone of Eldoria", "Elixir of Vitality", "Shadow Cloak", "Silver Longsword"],
        "locations": ["Crystal Catacombs", "Dragon's Ridge", "Forgotten Sanctum", "Moonlit Hollow"],
        "choices": [
            "Channel your energy into the glowing sigil",
            "Draw your weapon and advance cautiously into the catacombs",
            "Search the surrounding crumbled pillars for hidden relics"
        ]
    },
    "sci-fi": {
        "intro": "Emergency sirens pulse across Deck 9 of the derelict star cruiser Aegis. The mainframe's AI flickers online, warning of an anomalous void entity breaching the reactor core.",
        "image": "cyberpunk spaceship corridor emergency sirens neon holographic console",
        "items": ["Plasma Cutter", "Quantum Battery", "Neural Uplink", "Nano-Medkit"],
        "locations": ["Sub-level Reactor", "Command Bridge", "Airlock Chamber", "Hydroponics Bay"],
        "choices": [
            "Override the reactor terminal to seal the blast doors",
            "Equip your plasma cutter and investigate the anomalous signal",
            "Scan the corridor for power reroute nodes"
        ]
    },
    "horror": {
        "intro": "Rain lashes against the shattered stained glass of Ravenshollow Manor. The grandfather clock strikes thirteen, and wet footsteps echo from the attic above.",
        "image": "dark gothic Victorian mansion thunderstorm haunted shadows candlelit",
        "items": ["Brass Lantern", "Ancient Grimoire", "Salt Pouch", "Iron Skeleton Key"],
        "locations": ["Cellar Archives", "Attic Laboratory", "Overgrown Cemetery", "Mirror Gallery"],
        "choices": [
            "Raise your lantern and slowly ascend the creaking stairs",
            "Barricade the parlor door and search for an exit",
            "Inspect the strange symbols scrawled in ash across the floor"
        ]
    },
    "mystery": {
        "intro": "Fog rolls thick through the gaslit cobblestones of Victorian London. Inside the locked study of Lord Sterling, a poisoned chalice sits beside a burned ledger.",
        "image": "Victorian London foggy cobblestone gaslit street noir detective mystery",
        "items": ["Magnifying Monocle", "Cipher Notebook", "Pocket Watch", "Torn Letter"],
        "locations": ["Lord Sterling's Study", "The Docks Warehouse", "Underground Speakeasy", "Scotland Yard Archive"],
        "choices": [
            "Dust the chalice and ledger for latent fingerprints",
            "Examine the study window for signs of forced entry",
            "Interrogate the nervous butler standing by the foyer"
        ]
    },
    "western": {
        "intro": "Dust devils kick across the sun-scorched dirt of Desolation Ridge. The clocktower strikes noon, and shadows lengthen as the notorious Red Jack gang surrounds the town square.",
        "image": "wild west dusty frontier town midday standoff cinematic saloon",
        "items": ["Custom Revolver", "Dynamite Stick", "Silver Sheriff Badge", "Canteen of Fresh Water"],
        "locations": ["The Dusty Saloon", "Abandoned Silver Mine", "Sheriff's Jailhouse", "Canyon Pass"],
        "choices": [
            "Step into the dusty street and stare down the gang leader",
            "Take cover behind the saloon barrels and ready your rifle",
            "Slip around through the livery stables for an ambush"
        ]
    },
    "mythology": {
        "intro": "Mount Olympus trembles under an eclipse of blood. Hermes' broken staff lies shattered before you, and thunder rumbles with the wrath of forgotten titans.",
        "image": "Greek mythology Mount Olympus golden temple storm clouds divine lightning",
        "items": ["Aegis Shard", "Golden Ambrosia", "Feather of Pegasus", "Thunderstone"],
        "locations": ["Temple of Zeus", "Gates of Tartarus", "Oracle's Spring", "Elysian Meadows"],
        "choices": [
            "Pray at the golden altar for divine intervention",
            "Ascend the marbled stairs toward the celestial throne",
            "Examine the glowing fracture spreading across the temple floor"
        ]
    }
}

def generate_adaptive_state(genre="fantasy", name="Hero", choice="", prev_state=None, emotion="calm"):
    genre_data = GENRE_BEATS.get(genre, GENRE_BEATS["fantasy"])
    
    if not prev_state:
        # Starting scene
        return {
            "story": f"{genre_data['intro']} You, {name}, stand at the precipice of destiny with your pulse racing.",
            "image_prompt": genre_data["image"],
            "choices": genre_data["choices"],
            "hp": 100,
            "max_hp": 100,
            "inventory": [],
            "emotion": "tense",
            "game_over": False,
            "victory": False,
            "death_message": "",
            "victory_message": ""
        }

    # Turn progression
    hp = prev_state.get("hp", 100)
    inventory = list(prev_state.get("inventory", []))
    
    # Emotion dynamics
    choice_lower = choice.lower()
    if any(k in choice_lower for k in ["attack", "override", "strike", "smash", "charge", "fire"]):
        event_emotion = "excited"
        hp_delta = -15 if random.random() < 0.6 else -5
        reaction = f"With fierce resolve, you unleash your attack against the threat! Sparks fly and tremors rock the ground."
    elif any(k in choice_lower for k in ["careful", "inspect", "search", "dust", "scan", "examine", "cautious"]):
        event_emotion = "calm"
        hp_delta = 5 if hp < 100 else 0
        reaction = f"Taking a deliberate breath, you analyze the surroundings. Your keen senses unveil critical secrets obscured in the dark."
    elif any(k in choice_lower for k in ["run", "hide", "flee", "barricade", "cover", "retreat"]):
        event_emotion = "fearful"
        hp_delta = -10
        reaction = f"Your heart pounds in your chest as you dive for cover, narrowly evading a devastating shockwave."
    else:
        event_emotion = "tense"
        hp_delta = -10 if random.random() < 0.5 else 0
        reaction = f"You commit to the maneuver. The environment shifts violently around you as the balance of power changes."

    hp = max(0, min(100, hp + hp_delta))

    # Add item discovery chance
    available_items = [it for it in genre_data["items"] if it not in inventory]
    found_item_text = ""
    if available_items and random.random() < 0.4:
        new_item = random.choice(available_items)
        inventory.append(new_item)
        found_item_text = f" Amid the chaos, you secure a valuable artifact: [{new_item}]."

    # End conditions
    if hp <= 0:
        return {
            "story": f"{reaction} The overwhelming onslaught proves too much. Darkness closes in as your strength completely fades.",
            "image_prompt": f"dramatic defeat cinematic dark mysterious {genre}",
            "choices": ["The end"],
            "hp": 0,
            "max_hp": 100,
            "inventory": inventory,
            "emotion": "grieving",
            "game_over": True,
            "victory": False,
            "death_message": f"Your quest ended in the depths of {random.choice(genre_data['locations'])}. The realm remembers your courage.",
            "victory_message": ""
        }

    if len(inventory) >= 3 and random.random() < 0.5:
        return {
            "story": f"{reaction}{found_item_text} Harnessing the artifacts you've gathered, you strike the final decisive blow, banishing the darkness once and for all!",
            "image_prompt": f"triumphant heroic victory radiant light epic {genre}",
            "choices": ["Celebrate victory"],
            "hp": hp,
            "max_hp": 100,
            "inventory": inventory,
            "emotion": "triumphant",
            "game_over": False,
            "victory": True,
            "death_message": "",
            "victory_message": f"Hail {name}! You conquered the trials of the {genre.title()} realm and carved your name into legend!"
        }

    # Generate next dynamic choices
    loc = random.choice(genre_data["locations"])
    next_choices = [
        f"Push further into the {loc} to press your advantage",
        f"Use your resources to fortify your position and recover",
        f"Activate your skills to uncover alternate passageways"
    ]

    return {
        "story": f"{reaction}{found_item_text} The path ahead leads directly toward the {loc}.",
        "image_prompt": f"cinematic scene {genre} {loc} atmospheric lighting high quality",
        "choices": next_choices,
        "hp": hp,
        "max_hp": 100,
        "inventory": inventory,
        "emotion": event_emotion,
        "game_over": False,
        "victory": False,
        "death_message": "",
        "victory_message": ""
    }

# ── IMAGE GENERATION ───────────────────────────────────────────────────────
#
# WHY "Vision Obscured" was happening — CORS:
#   The browser's fetch() API enforces CORS (Cross-Origin Resource Sharing).
#   When JS called fetch("https://lexica.art/...") or fetch("https://source.unsplash.com/..."),
#   those servers do not send Access-Control-Allow-Origin headers, so the
#   browser hard-blocks the response. Every attempt failed → "Vision Obscured".
#   source.unsplash.com was also permanently shut down in 2023.
#
# THE FIX — resolve the image URL server-side in Python (Flask), not in JS:
#   Python/Flask has ZERO CORS restrictions — it fetches any URL freely.
#   We call Lexica from Python, get the direct CDN image URL, and send
#   just that URL string back to the browser in the JSON response.
#   The browser then sets img.src = thatUrl — and <img> elements load
#   cross-origin images freely (CORS only blocks fetch/XHR, never <img>).
#
# IMAGE SOURCES (server-side, both 100% free, no API key):
#   1. Lexica.art  — real AI-generated art matched to the scene prompt.
#                    Pre-generated cache = instant, no generation wait.
#   2. Picsum      — beautiful seeded photography, sub-100ms, never fails.
#                    Used when Lexica has no results or times out.

def _clean_keywords(prompt: str) -> str:
    stop = r'\b(a|an|the|and|of|in|on|at|with|from|by|for|is|are|was|were|cinematic|scene|dramatic|epic|dark|mysterious|atmosphere)\b'
    clean = re.sub(stop, '', prompt.lower())
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:80] if clean else prompt[:80]

def get_image_url(prompt: str) -> str:
    """
    Resolves a themed image URL on the server side.
    Returns a direct image URL. Browser sets img.src = this. No CORS ever.
    Never raises — always returns a valid URL.
    """
    # ── Primary: Lexica.art (AI art, themed, instant from cache) ──────────
    try:
        keywords = _clean_keywords(prompt)
        safe     = urllib.parse.quote(keywords)
        resp     = requests.get(
            f"https://lexica.art/api/v1/images?q={safe}",
            timeout=6,
            headers={"User-Agent": "Mozilla/5.0 (compatible; DungeonMaster/1.0)"}
        )
        if resp.ok:
            images = resp.json().get("images", [])
            pool   = [img for img in images[:4] if img.get("src")]
            if pool:
                return random.choice(pool)["src"]
    except Exception:
        pass

    # ── Fallback: Picsum Photos (guaranteed, beautiful, seeded by prompt) ──
    seed = abs(hash(prompt)) % 9999
    return f"https://picsum.photos/seed/{seed}/800/450"


# ── Helpers ────────────────────────────────────────────────────────────────
def parse_json(raw: str):
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None

def validate(state: dict) -> bool:
    return isinstance(state, dict) and all(k in state for k in REQUIRED_KEYS)

def call_groq(messages: list):
    if not GROQ_API_KEY:
        return None, "no_groq_key"
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "temperature": 0.8,
            "response_format": {"type": "json_object"}
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=25)
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"].strip(), None
    except Exception as e:
        pass
    return None, "groq_failed"

def call_ollama(messages: list) -> tuple:
    payload = {
        "model":    MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "stream":   False,
        "options":  {"temperature": 0.9, "num_predict": 1024}
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip(), None

def safe_generate(messages: list):
    if GROQ_API_KEY:
        raw, err = call_groq(messages)
        if raw:
            state = parse_json(raw)
            if state and validate(state):
                return state, raw

    for attempt in range(2):
        try:
            raw, err = call_ollama(messages)
            state = parse_json(raw)
            if state and validate(state):
                return state, raw
        except requests.exceptions.ConnectionError:
            break
        except Exception:
            pass
    return None, "__ollama_down__"

def build_start_prompt(genre: str, name: str) -> str:
    return (
        f"Start a new {genre} adventure for a hero named {name}. "
        "Open dramatically: vivid world, immediate danger, a looming quest. "
        "HP=100, inventory empty. Respond with JSON only."
    )

def build_emotion_context(choice, player_emotion, dm_instruction, persistence_note):
    note = f" {persistence_note}" if persistence_note else ""
    return (
        f'Player chose: "{choice}"\n'
        f"Player mood: {player_emotion['dominant'].upper()} "
        f"(intensity {player_emotion['intensity']}/3){note}\n"
        f"DM tone: {dm_instruction['tone']}\n"
        f"DM mechanic: {dm_instruction['mechanics']}\n"
        "Respond with JSON only."
    )

# ── Routes ─────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    if GROQ_API_KEY:
        return jsonify({"ollama": "running", "model": "llama-3.1 (Groq Cloud)", "ready": True, "mode": "cloud"})

    try:
        base_url = OLLAMA_URL.rsplit("/api", 1)[0]
        r = requests.get(f"{base_url}/api/tags", timeout=2)
        if r.ok:
            models = [m["name"] for m in r.json().get("models", [])]
            has_model = any(MODEL in m for m in models)
            return jsonify({"ollama": "running", "model": MODEL, "ready": has_model, "models": models, "mode": "ollama"})
    except Exception:
        pass

    # Cloud / Render Adaptive Engine mode
    return jsonify({
        "ollama": "running",
        "model": "Adaptive RPG Engine (Cloud Live)",
        "ready": True,
        "mode": "adaptive"
    })

@app.route("/start", methods=["POST"])
def start_game():
    data  = request.json or {}
    genre = data.get("genre", "fantasy")
    name  = data.get("character_name", "Hero")

    session.clear()
    session["genre"]           = genre
    session["character_name"]  = name
    session["emotion_history"] = []

    history    = [{"role": "user", "content": build_start_prompt(genre, name)}]
    state, raw = safe_generate(history)

    if not state:
        state = generate_adaptive_state(genre=genre, name=name)
        raw   = json.dumps(state)

    history.append({"role": "assistant", "content": raw})
    session["history"]    = history
    session["last_state"] = state

    # Server resolves image — browser just sets img.src, zero CORS risk
    state["image_url"]                = get_image_url(state.get("image_prompt", f"{genre} scene"))
    state["player_emotion"]           = "neutral"
    state["player_emotion_intensity"] = 1
    state["persistence_active"]       = False

    return jsonify(state)

@app.route("/action", methods=["POST"])
def take_action():
    data    = request.json or {}
    choice  = data.get("choice", "")
    history = session.get("history", [])

    if not history:
        return jsonify({"error": "No active game. Please start a new game."}), 400

    player_emotion   = emotion_engine.analyze(choice)
    dm_instruction   = emotion_engine.get_dm_instruction(player_emotion)

    emotion_history = session.get("emotion_history", [])
    emotion_history.append(player_emotion["dominant"])
    emotion_history = emotion_history[-3:]
    session["emotion_history"] = emotion_history
    persistence_note = emotion_engine.build_persistence_note(emotion_history)

    ctx = build_emotion_context(choice, player_emotion, dm_instruction, persistence_note)
    history.append({"role": "user", "content": ctx})
    history = history[-10:]

    state, raw = safe_generate(history)

    genre = session.get("genre", "fantasy")
    name  = session.get("character_name", "Hero")
    if not state:
        prev_state = session.get("last_state")
        state = generate_adaptive_state(genre=genre, name=name, choice=choice, prev_state=prev_state, emotion=player_emotion["dominant"])
        raw   = json.dumps(state)

    state["player_emotion"]           = player_emotion["dominant"]
    state["player_emotion_intensity"] = player_emotion["intensity"]
    state["emotion_signals"]          = player_emotion["detected_signals"]
    state["persistence_active"]       = bool(persistence_note)

    history.append({"role": "assistant", "content": raw})
    session["history"]    = history
    session["last_state"] = state

    # Server resolves image — browser just sets img.src, zero CORS risk
    state["image_url"] = get_image_url(state.get("image_prompt", "epic fantasy scene"))
    return jsonify(state)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "="*54)
    print("  AI DUNGEON MASTER — Live & Local Edition")
    print("="*54)
    print(f"  Model  : {MODEL}")
    print(f"  Port   : {port}")
    print("="*54 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False)