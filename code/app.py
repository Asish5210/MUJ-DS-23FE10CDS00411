from flask import Flask, render_template, request, jsonify, session
import requests
import json
import re
import random
import urllib.parse
from emotion_engine import PlayerEmotionEngine

app = Flask(__name__)
app.secret_key = "dungeon-master-secret-x7k2"
emotion_engine = PlayerEmotionEngine()

# ── Ollama config ──────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "llama3.2"

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

# ── Fallback state ─────────────────────────────────────────────────────────
def fallback_state(genre="fantasy"):
    return {
        "story": "The world trembles. A shadow passes over the land. Something stirs in the darkness ahead — your quest is not yet over.",
        "image_prompt": f"dark mysterious {genre} landscape, ominous atmosphere, cinematic",
        "choices": ["Press forward into the unknown", "Stop and assess your surroundings", "Search for another path"],
        "hp": 100, "max_hp": 100, "inventory": [],
        "emotion": "tense", "game_over": False, "victory": False,
        "death_message": "", "victory_message": ""
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
    for attempt in range(3):
        try:
            raw, err = call_ollama(messages)
            state = parse_json(raw)
            if state and validate(state):
                return state, raw
        except requests.exceptions.ConnectionError:
            return None, "__ollama_down__"
        except Exception:
            pass
    return None, "__parse_failed__"

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
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        has_model = any(MODEL in m for m in models)
        return jsonify({"ollama": "running", "model": MODEL, "ready": has_model, "models": models})
    except Exception as e:
        return jsonify({"ollama": "offline", "error": str(e)}), 503

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

    if raw == "__ollama_down__":
        return jsonify({"error": "OLLAMA_OFFLINE"}), 503

    if not state:
        state = fallback_state(genre)
        raw   = json.dumps(state)

    history.append({"role": "assistant", "content": raw})
    session["history"] = history

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

    if raw == "__ollama_down__":
        return jsonify({"error": "OLLAMA_OFFLINE"}), 503

    genre = session.get("genre", "fantasy")
    if not state:
        state = fallback_state(genre)
        raw   = json.dumps(state)

    state["player_emotion"]           = player_emotion["dominant"]
    state["player_emotion_intensity"] = player_emotion["intensity"]
    state["emotion_signals"]          = player_emotion["detected_signals"]
    state["persistence_active"]       = bool(persistence_note)

    history.append({"role": "assistant", "content": raw})
    session["history"] = history

    # Server resolves image — browser just sets img.src, zero CORS risk
    state["image_url"] = get_image_url(state.get("image_prompt", "epic fantasy scene"))
    return jsonify(state)

if __name__ == "__main__":
    print("\n" + "="*54)
    print("  AI DUNGEON MASTER — Ollama Local Edition")
    print("="*54)
    print(f"  Model  : {MODEL}")
    print(f"  Ollama : {OLLAMA_URL}")
    print("  Open   : http://localhost:5000")
    print("="*54 + "\n")
    app.run(debug=True)