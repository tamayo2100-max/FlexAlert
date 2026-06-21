"""
matcher.py  -  Decide si un bloque cumple TUS filtros.

Recibe un bloque (de notification_parser) y la config de filtros (de db),
y devuelve (cumple: bool, razon: str).

Este es el "portero": solo deja pasar (y por tanto solo dispara la alarma)
los bloques que de verdad te interesan.
"""


def match_block(block: dict, filters: dict) -> tuple[bool, str]:
    # --- Pago por hora minimo ---
    min_pay = float(filters.get("min_pay_hour") or 0)
    if min_pay > 0:
        ph = block.get("pay_hour")
        if ph is None and block.get("pay") and block.get("duration"):
            ph = block["pay"] / block["duration"]
        if ph is None:
            return False, "no se pudo calcular $/hora"
        if ph < min_pay:
            return False, f"${ph:.1f}/h por debajo de tu minimo (${min_pay:.0f}/h)"

    # --- Estaciones ---
    stations = filters.get("stations") or []
    if stations:
        st = block.get("station")
        if st not in stations:
            return False, f"estacion {st or '?'} no esta en tu lista"

    # --- Horario de inicio ---
    ts, te = filters.get("time_start"), filters.get("time_end")
    if ts and te:
        bt = block.get("start_time")
        if bt is None:
            return False, "sin hora de inicio para comparar"
        if not (ts <= bt <= te):
            return False, f"inicio {bt} fuera de tu horario ({ts}-{te})"

    # --- Duracion ---
    dur = block.get("duration")
    dmin = float(filters.get("dur_min") or 0)
    dmax = float(filters.get("dur_max") or 0)
    if dmin > 0:
        if dur is None or dur < dmin:
            return False, f"duracion {dur or '?'}h menor a tu minimo ({dmin:g}h)"
    if dmax > 0:
        if dur is None or dur > dmax:
            return False, f"duracion {dur or '?'}h mayor a tu maximo ({dmax:g}h)"

    return True, "cumple todos tus filtros"
