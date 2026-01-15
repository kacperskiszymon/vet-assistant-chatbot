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
    day = now.weekday()
    time_now = now.strftime("%H:%M")

    if OPENING_HOURS[day] is None:
        return "SUNDAY", time_now

    open_time, close_time = OPENING_HOURS[day]
    if open_time <= time_now <= close_time:
        return "OPEN", time_now
    return "CLOSED", time_now


SYSTEM_PROMPT_BASE = """
Jesteś inteligentnym Asystentem Przychodni Weterynaryjnej działającym w trybie demonstracyjnym.

WAŻNE:
- NIE jesteś lekarzem
- NIE stawiasz diagnoz
- NIE podajesz nazw leków ani dawek
- NIE wykonujesz zabiegów

WOLNO CI:
- logicznie rozumować
- wyjaśniać OGÓLNIE, czym jest opisywany problem (edukacyjnie)
- tłumaczyć, dlaczego samodzielne leczenie może zaszkodzić
- prowadzić rozmowę jak doświadczona recepcja, nie automat

ZASADY ROZMOWY:
- NIE powtarzaj w kółko tych samych zdań
- jeśli użytkownik dopytuje „co robić” – ROZWIŃ odpowiedź
- reaguj adekwatnie do treści pytania
- dostosuj odpowiedź do pory dnia i godzin pracy
- podawaj AKTUALNĄ GODZINĘ, jeśli gabinet jest zamknięty

STYL:
- spokojny
- ludzki
- wspierający
- bez straszenia
- bez formułek

Jeśli pytanie dotyczy:
- szczepień, cen, terminów → poinformuj, że w wersji demo brak szczegółowych danych
- problemów zdrowotnych → edukuj ogólnie, nie diagnozuj

Twoim celem jest, aby rozmowa brzmiała jak rozmowa z mądrą,
doświadczoną recepcją weterynaryjną.
"""

SUNDAY_RULES = """
Dziś jest niedziela, gabinet jest nieczynny.

Twoja odpowiedź powinna:
- wyraźnie uspokajać właściciela
- zalecać spokój, ciszę i brak stresu dla zwierzęcia
- NIE zalecać karmienia na siłę
- podkreślać znaczenie stałego dostępu do świeżej wody
- poinformować, że sprawa zostanie omówiona po otwarciu gabinetu
"""

CLOSED_RULES = """
Gabinet jest obecnie zamknięty.

Twoja odpowiedź powinna:
- poinformować o aktualnej godzinie
- jasno powiedzieć, że gabinet jest nieczynny
- uspokoić właściciela
- zalecić spokój, ciszę i obserwację zwierzęcia
- NIE zalecać leczenia na własną rękę
- zasugerować kontakt po otwarciu gabinetu
"""

OPEN_RULES = """
Gabinet jest obecnie czynny.

Twoja odpowiedź powinna:
- być spokojna i rzeczowa
- naturalnie zasugerować możliwość kontaktu z personelem
- NIE wywierać presji
"""


@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "reply": "Witaj, jestem Asystentem Przychodni. Jak mogę pomóc?"
        })

    time_context, current_time = get_time_context()

    system_prompt = SYSTEM_PROMPT_BASE

    if time_context == "SUNDAY":
        system_prompt += f"\nAktualna godzina: {current_time}\n" + SUNDAY_RULES
    elif time_context == "CLOSED":
        system_prompt += f"\nAktualna godzina: {current_time}\n" + CLOSED_RULES
    else:
        system_prompt += OPEN_RULES

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        temperature=0.35
    )

    reply = completion.choices[0].message.content
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
