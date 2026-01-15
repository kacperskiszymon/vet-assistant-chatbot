from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import os
from datetime import datetime

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ====== DEMO PAMIĘĆ ======
USER_STATE = {}        # ip -> state
CONTACT_REQUESTS = []  # zapisane kontakty

STATE_NORMAL = "NORMAL"
STATE_WAITING_CONTACT = "WAITING_CONTACT"
STATE_CONTACT_SAVED = "CONTACT_SAVED"

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
        status = "SUNDAY"
    else:
        open_t, close_t = OPENING_HOURS[weekday]
        status = "OPEN" if open_t <= time_now <= close_t else "CLOSED"

    return greeting, status, time_now


SYSTEM_PROMPT = """
Jesteś Asystentem Przychodni Weterynaryjnej.

ZASADY BEZWZGLĘDNE:
- nie powtarzaj w kółko tych samych pytań
- jeśli użytkownik podał dane kontaktowe — POTWIERDŹ I ZAKOŃCZ TEMAT
- mów spokojnie, empatycznie i po ludzku
- NIE stawiaj diagnoz
- NIE podawaj leków

Jeśli użytkownik opisuje uraz:
- nazwij emocje
- zalecaj spokój, ograniczenie ruchu, wodę
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

    # Inicjalizacja stanu
    if user_ip not in USER_STATE:
        USER_STATE[user_ip] = STATE_NORMAL

    # START ROZMOWY
    if msg_lower == "__start__":
        USER_STATE[user_ip] = STATE_NORMAL
        return jsonify({
            "reply": f"{greeting}, jestem Asystentem Przychodni Weterynaryjnej. Jak mogę pomóc?"
        })

    # ====== TRYB OCZEKIWANIA NA KONTAKT ======
    if USER_STATE[user_ip] == STATE_WAITING_CONTACT:
        if any(char.isdigit() for char in message) or "@" in message:
            CONTACT_REQUESTS.append({
                "ip": user_ip,
                "time": datetime.now().isoformat(),
                "contact": message
            })
            USER_STATE[user_ip] = STATE_CONTACT_SAVED
            return jsonify({
                "reply": (
                    "Dziękuję, dane kontaktowe zostały zapisane. "
                    "Rozmowa zostanie przekazana do przychodni, a pracownik "
                    "skontaktuje się z Tobą, gdy tylko będzie to możliwe. "
                    "Jeśli chcesz, możesz jeszcze spokojnie opisać sytuację zwierzęcia."
                )
            })
        else:
            return jsonify({
                "reply": "Proszę podać numer telefonu lub adres e-mail, abym mógł przekazać kontakt do przychodni."
            })

    # ====== INTENCJA ZOSTAWIENIA KONTAKTU ======
    if any(kw in msg_lower for kw in ["kontakt", "numer", "telefon", "email", "e-mail", "skontaktujecie"]):
        USER_STATE[user_ip] = STATE_WAITING_CONTACT
        return jsonify({
            "reply": (
                "Oczywiście. Proszę podać numer telefonu lub adres e-mail. "
                "Ta rozmowa zostanie przekazana do przychodni, a pracownik skontaktuje się z Tobą, "
                "gdy tylko będzie to możliwe."
            )
        })

    # ====== INFO O ZAMKNIĘCIU ======
    status_info = ""
    if status in ["CLOSED", "SUNDAY"]:
        status_info = (
            f"Jest godzina {current_time}, przychodnia jest obecnie zamknięta. "
            "Rozumiem, że to bardzo stresujące — spróbujmy na chwilę wziąć spokojny, głęboki oddech. "
            "Na teraz najważniejszy jest spokój, ograniczenie ruchu zwierzęcia i dostęp do świeżej wody. "
        )

    # ====== ODPOWIEDŹ AI ======
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": status_info},
            {"role": "user", "content": message}
        ],
        temperature=0.4
    )

    return jsonify({"reply": completion.choices[0].message.content})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
