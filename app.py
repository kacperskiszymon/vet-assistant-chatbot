from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import os
from datetime import datetime

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# GODZINY OTWARCIA
OPENING_HOURS = {
    0: ("08:00", "18:00"),  # poniedziałek
    1: ("08:00", "18:00"),  # wtorek
    2: ("08:00", "18:00"),  # środa
    3: ("08:00", "18:00"),  # czwartek
    4: ("08:00", "16:00"),  # piątek
    5: ("08:00", "13:00"),  # sobota
    6: None                 # niedziela – zamknięte
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


SYSTEM_PROMPT_BASE = """
Jesteś inteligentnym Asystentem Przychodni Weterynaryjnej (wersja demonstracyjna).

ZASADY KLUCZOWE:
- POWITANIE JEST TYLKO JEDNO NA ROZMOWĘ
- jeśli użytkownik napisze: „witaj”, „dzień dobry”, „dobry wieczór”
  odpowiedz krótko i przejdź do pomocy
- NIE powtarzaj pełnego powitania

NIE WOLNO:
- stawiać diagnoz
- podawać nazw leków ani dawek
- sugerować leczenia na własną rękę

WOLNO:
- ogólnie wyjaśniać, czym jest opisywany problem
- tłumaczyć, dlaczego samodzielne leczenie może pogorszyć sytuację
- reagować empatycznie i różnicować odpowiedzi

STYL:
- spokojny
- ludzki
- wspierający
- bez straszenia
- bez automatycznych formułek

W SYTUACJACH STRESOWYCH:
- nazwij emocje („rozumiem, że to trudne”)
- zaproponuj chwilę spokojnego, głębokiego oddechu
- zachęć do zachowania spokoju
"""


@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message_raw = data.get("message", "")
    message = message_raw.strip().lower()

    greeting, status, current_time = get_time_context()

    # TECHNICZNY START ROZMOWY (wysyłany przez frontend)
    if message == "__start__":
        return jsonify({
            "reply": f"{greeting}, jestem Asystentem Przychodni Weterynaryjnej. Jak mogę pomóc?"
        })

    status_info = ""
    if status in ["CLOSED", "SUNDAY"]:
        status_info = (
            f"\nJest godzina {current_time}, gabinet jest obecnie zamknięty. "
            "Rozumiem, że to może być trudne — spróbujmy na chwilę wziąć spokojny, głęboki oddech. "
            "Na teraz najważniejszy jest spokój i uważna obserwacja zwierzęcia. "
            "Zapewnij dostęp do świeżej wody i skontaktuj się z gabinetem po otwarciu."
        )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT_BASE + status_info
            },
            {
                "role": "user",
                "content": message_raw
            }
        ],
        temperature=0.4
    )

    reply = completion.choices[0].message.content
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
