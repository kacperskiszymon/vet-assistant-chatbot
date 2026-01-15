from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import os
from datetime import datetime
import re

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ====== STANY ======
STATE_NORMAL = "NORMAL"
STATE_WAITING_CONTACT = "WAITING_CONTACT"
STATE_CONTACT_SAVED = "CONTACT_SAVED"

USER_STATE = {}
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

SYSTEM_PROMPT = """
Jesteś Asystentem Przychodni Weterynaryjnej.
Mów spokojnie, empatycznie, jak do człowieka.
NIE pytaj ponownie o dane kontaktowe, jeśli zostały zapisane.
"""

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_ip = request.remote_addr
    data = request.json
    message = data.get("message", "").strip()
    msg_lower = message.lower()

    greeting, status, current_time = get_time_context()

    if user_ip not in USER_STATE:
        USER_STATE[user_ip] = STATE_NORMAL

    # START
    if msg_lower == "__start__":
        USER_STATE[user_ip] = STATE_NORMAL
        return jsonify({
            "reply": f"{greeting}, jestem Asystentem Przychodni Weterynaryjnej. Jak mogę pomóc?"
        })

    # ====== KONTAKT JUŻ ZAPISANY — BLOKADA AI ======
    if USER_STATE[user_ip] == STATE_CONTACT_SAVED:
        return jsonify({
            "reply": (
                "Masz rację — zapisałem Twoje dane kontaktowe. "
                "Przepraszam, że wcześniej dopytywałem. "
                "Rozmowa została przekazana do przychodni i pracownik "
                "skontaktuje się z Tobą, gdy tylko będzie to możliwe. "
                "Jeśli chcesz, możemy teraz spokojnie skupić się na tym, "
                "jak najlepiej zadbać o zwierzę do czasu wizyty."
            )
        })

    # ====== OCZEKIWANIE NA KONTAKT ======
    if USER_STATE[user_ip] == STATE_WAITING_CONTACT:
        if contains_contact(message):
            CONTACT_REQUESTS.append({
                "ip": user_ip,
                "time": datetime.now().isoformat(),
                "contact": message
            })
            USER_STATE[user_ip] = STATE_CONTACT_SAVED
            return jsonify({
                "reply": (
                    "Dziękuję, zapisałem Twoje dane kontaktowe. "
                    "Rozmowa została przekazana do przychodni. "
                    "Pracownik skontaktuje się z Tobą, gdy tylko będzie to możliwe."
                )
            })
        else:
            return jsonify({
                "reply": "Proszę podać numer telefonu lub adres e-mail."
            })

    # ====== INTENCJA ZOSTAWIENIA KONTAKTU ======
    if any(k in msg_lower for k in ["kontakt", "numer", "telefon", "email", "e-mail", "umówić"]):
        USER_STATE[user_ip] = STATE_WAITING_CONTACT
        return jsonify({
            "reply": (
                "Rozumiem. Proszę podać numer telefonu lub adres e-mail. "
                "Rozmowa zostanie przekazana do przychodni."
            )
        })

    # ====== NORMALNA ODPOWIEDŹ AI ======
    status_info = ""
    if status == "CLOSED":
        status_info = (
            f"Jest godzina {current_time}. Przychodnia jest obecnie zamknięta. "
            "Rozumiem, że to trudne — weźmy spokojny, głęboki oddech. "
            "Na teraz najważniejszy jest spokój, ograniczenie ruchu i woda."
        )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": status_info},
            {"role": "user", "content": message}
        ],
        temperature=0.35
    )

    return jsonify({"reply": completion.choices[0].message.content})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
