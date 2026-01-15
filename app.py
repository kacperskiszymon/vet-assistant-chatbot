from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import os
from datetime import datetime

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- DEMO STORAGE (w pamięci) ---
CONTACT_REQUESTS = []

# GODZINY OTWARCIA
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
Jesteś inteligentnym Asystentem Przychodni Weterynaryjnej (wersja demonstracyjna).

ZASADY:
- mów spokojnie i po ludzku
- NIE stawiaj diagnoz
- NIE podawaj leków
- możesz przyjąć dane kontaktowe właściciela
- ZAWSZE jasno informuj, że rozmowa zostanie przekazana do przychodni

Jeśli użytkownik chce zostawić kontakt:
- poproś o imię i numer telefonu lub e-mail
- potwierdź, że dane zostaną przekazane personelowi
"""

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").strip()

    greeting, status, current_time = get_time_context()
    msg_lower = message.lower()

    # START ROZMOWY
    if msg_lower == "__start__":
        return jsonify({
            "reply": f"{greeting}, jestem Asystentem Przychodni Weterynaryjnej. Jak mogę pomóc?"
        })

    # INTENCJA: ZOSTAWIENIE KONTAKTU
    if any(kw in msg_lower for kw in ["kontakt", "numer", "telefon", "email", "e-mail", "skontaktujecie"]):
        return jsonify({
            "reply": (
                "Oczywiście. Proszę podać imię oraz numer telefonu lub adres e-mail. "
                "Ta rozmowa zostanie przekazana do przychodni, a pracownik skontaktuje się z Tobą, "
                "gdy tylko będzie to możliwe."
            )
        })

    # WYKRYCIE DANYCH KONTAKTOWYCH (proste demo)
    if any(char.isdigit() for char in message) or "@" in message:
        CONTACT_REQUESTS.append({
            "time": datetime.now().isoformat(),
            "contact": message
        })
        return jsonify({
            "reply": (
                "Dziękuję. Dane kontaktowe zostały zapisane. "
                "Rozmowa zostanie przekazana do przychodni i pracownik skontaktuje się z Tobą, "
                "gdy tylko będzie to możliwe."
            )
        })

    # INFO O ZAMKNIĘCIU
    status_info = ""
    if status in ["CLOSED", "SUNDAY"]:
        status_info = (
            f"Jest godzina {current_time}, przychodnia jest obecnie zamknięta. "
            "Rozumiem, że to bardzo stresujące — spróbujmy na chwilę wziąć spokojny, głęboki oddech. "
            "Na teraz najważniejszy jest spokój, ograniczenie ruchu zwierzęcia i dostęp do świeżej wody. "
        )

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
