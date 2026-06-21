"""
notification_parser.py  -  Convierte el texto de una notificacion de
Amazon Flex en un "bloque" estructurado (pago, duracion, estacion, hora).

Es tolerante: los formatos de notificacion varian, asi que extrae lo que
pueda. Si no logra sacar ni pago ni duracion, devuelve None.

NOTA: esto NO automatiza nada en Amazon. Solo LEE el texto de una
notificacion que Amazon ya te mando, para decidir si vale la pena avisarte.
"""

import re


def parse_notification(text: str) -> dict | None:
    if not text:
        return None

    # --- Pago total ($) ---
    pay = None
    m = re.search(r"\$\s?(\d+(?:[.,]\d{1,2})?)", text)
    if m:
        pay = float(m.group(1).replace(",", "."))

    # --- Duracion (horas) ---  ej: "3 hr", "3 hours", "2.5 horas", "3 hr 30 min"
    hours = 0.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:hrs?|hours?|horas?|h)\b", text, re.I)
    if m:
        hours = float(m.group(1))
    minutes = 0.0
    m = re.search(r"(\d+)\s*(?:mins?|minutos?|m)\b", text, re.I)
    if m:
        minutes = float(m.group(1))
    duration = (hours + minutes / 60.0) if (hours or minutes) else None

    # --- Estacion ---  ej: DLA5, DAX8, VNY3
    station = None
    m = re.search(r"\b([A-Z]{2,4}\d{1,2})\b", text)
    if m:
        station = m.group(1)

    # --- Hora de inicio ---  ej: "6:00 AM", "14:30"
    start_time = None
    m = re.search(r"\b(\d{1,2}):(\d{2})\s*([AaPp][Mm])?", text)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
        ap = (m.group(3) or "").lower()
        if ap == "pm" and hh != 12:
            hh += 12
        elif ap == "am" and hh == 12:
            hh = 0
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            start_time = f"{hh:02d}:{mm:02d}"

    if pay is None and duration is None:
        return None  # no se pudo interpretar como oferta de bloque

    block = {
        "pay": pay,
        "duration": duration,
        "station": station,
        "start_time": start_time,
        "pay_hour": (pay / duration) if (pay and duration) else None,
    }
    return block
