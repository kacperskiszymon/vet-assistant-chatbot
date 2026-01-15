from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import os
from datetime import datetime
import re

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ====== FAZY ROZMOWY ======
PHASE_GENERAL = "GENERAL"
PHASE_COLLECT_CONTACT = "COLLECT_CONTACT"
PHASE_POST_CONTACT = "POST_CONTACT"
PHASE_PRE_VISIT_HELP = "PRE_VISIT_HELP"

CONVERSATIONS = {}
CONTACT_REQUESTS = []

# ====== GODZINY OTWARCIA ======
OPENING_HOURS = {
    0: ("08:00", "18:00"),
    1: ("08:00", "18:00"),
    2: ("08:00", "18:00"),
    3: ("08:00", "18:00"),
    4: ("08:00", "16:00"),
    5: ("08:00", "13:00"),
    6: None
}

SYSTEM_PROMPT_GENERAL = """
Jesteś Asystentem Przychodni Weterynaryjnej.
Mów spokojnie, empatycznie.
Nie stawiasz diagnoz.
"""

SYSTEM_PROMPT_PRE_VISIT = """
Jesteś Asystentem Przychodni Weterynaryjnej.
Pomagasz uspokoić opiekuna i podajesz bezpieczne, ogólne wskazówki
jak zadbać o zwierzę do czasu wizyty.
Nie stawiasz diagnoz.
Nie pytasz o dane kontaktowe.
"""

def get_time_context():
    now = datetime.now()
    weekday = now.weekday()
    time_now = now.strftime("%H:%M")
    hour = now.hour
    greeting = "Dzień dobry" if 6 <= hour < 18 else "Dobry wieczór"

    if OPENING_HOURS[weekday] is None:
        status = "CLOSED"
    else:
        open_t, close_t = OPENING_HOURS[weekday]
        status = "OPEN" if open_t <= time_now <= close_t else "CLOSED"

    return greeting, status, time_now

def contains_contact(text):
    email = re.search(r"\S+@\S+\.\S+", text)
    phone = re.search(r"\d{3}[\s\-]?\d{3}[\s\-]?\d{3}", text)
    return bool(email or phone)

def wants_contact(message):
    keywords = ["kontakt", "numer", "telefon", "email", "e-mail", "umówić", "wizyta"]
    return any(k in message for k in keywords)

def get_conversation(session_id):
    if session_id not in CONVERSATIONS:
        CONVERSATIONS[session_id] = {
            "phase": PHASE_GENERAL,
            "contact_saved": False,
            "contact_value": None
        }
    return CONVERSATIONS[session_id]

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    session_id = request.remote_addr
    data = request.json
    message = data.get("message", "").strip()
    msg_lower = message.lower()

    greeting, status, current_time = get_time_context()
    convo = get_conversation(session_id)

    # ====== START ======
    if msg_lower == "__start__":
        convo["phase"] = PHASE_GENERAL
        return jsonify({
            "reply": f"{greeting}, jestem Asystentem Przychodni Weterynaryjnej. Jak mogę pomóc?"
        })

    # ====== FAZA: ZBIERANIE KONTAKTU ======
    if convo["phase"] == PHASE_COLLECT_CONTACT:
        if contains_contact(message):
            convo["contact_saved"] = True
            convo["contact_value"] = message
            CONTACT_REQUESTS.append({
                "session": session_id,
                "time": datetime.now().isoformat(),
                "contact": message
            })
            convo["phase"] = PHASE_POST_CONTACT
            return jsonify({
                "reply": (
                    "Dziękuję, zapisałem dane kontaktowe. "
                    "Rozmowa została przekazana do przychodni."
                )
            })
        else:
            return jsonify({
                "reply": "Proszę podać numer telefonu lub adres e-mail."
            })

    # ====== FAZA: PO ZAPISIE KONTAKTU (JEDNORAZOWA) ======
    if convo["phase"] == PHASE_POST_CONTACT:
        convo["phase"] = PHASE_PRE_VISIT_HELP
        return jsonify({
            "reply": (
                "Jeśli chcesz, możemy teraz spokojnie skupić się na tym, "
                "jak pomóc zwierzęciu do czasu wizyty."
            )
        })

    # ====== FAZA: ROZMOWA OGÓLNA ======
    if convo["phase"] == PHASE_GENERAL:
        if not convo["contact_saved"] and wants_contact(msg_lower):
            convo["phase"] = PHASE_COLLECT_CONTACT
            return jsonify({
                "reply": (
                    "Rozumiem. Proszę podać numer telefonu lub adres e-mail. "
                    "Przekażemy sprawę do przychodni."
                )
            })

        status_info = ""
        if status == "CLOSED":
            status_info = (
                f"Jest godzina {current_time}. Przychodnia jest obecnie zamknięta. "
                "Postarajmy się zachować spokój."
            )

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_GENERAL},
                {"role": "assistant", "content": status_info},
                {"role": "user", "content": message}
            ],
            temperature=0.35
        )

        return jsonify({"reply": completion.choices[0].message.content})

    # ====== FAZA: POMOC DO CZASU WIZYTY ======
    if convo["phase"] == PHASE_PRE_VISIT_HELP:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_PRE_VISIT},
                {"role": "user", "content": message}
            ],
            temperature=0.35
        )

        return jsonify({"reply": completion.choices[0].message.content})

    return jsonify({"reply": "Chwileczkę, spróbujmy jeszcze raz."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
