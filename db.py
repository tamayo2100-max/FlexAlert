"""
db.py  -  Capa de datos de FlexAlert (SQLite local).

Guarda:
  - settings : la configuracion de filtros actual (clave/valor)
  - presets  : combos de filtros guardados con nombre

Todo queda en flexalert.db, junto a la app. No depende de internet.
"""

import os
import json
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "flexalert.db")

# Valores por defecto de los filtros (cuando no hay nada configurado)
DEFAULTS = {
    "min_pay_hour": 0.0,   # pago minimo por hora ($)
    "stations": [],        # lista de estaciones permitidas ([] = todas)
    "time_start": "",      # hora minima de inicio "HH:MM"
    "time_end": "",        # hora maxima de inicio "HH:MM"
    "dur_min": 0.0,        # duracion minima del bloque (horas)
    "dur_max": 0.0,        # duracion maxima del bloque (horas)
}


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Crea las tablas si no existen."""
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS settings ("
            "key TEXT PRIMARY KEY, value TEXT)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS presets ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT UNIQUE, config TEXT)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS blocks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "date TEXT, station TEXT, pay REAL, duration REAL, "
            "created_at TEXT)"
        )


def get_filters() -> dict:
    """Devuelve la config de filtros actual (con defaults rellenados)."""
    cfg = dict(DEFAULTS)
    with _conn() as c:
        for key, value in c.execute("SELECT key, value FROM settings"):
            try:
                cfg[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                cfg[key] = value
    return cfg


def set_filter(key: str, value) -> None:
    """Guarda/actualiza un filtro."""
    with _conn() as c:
        c.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )


def set_filters(cfg: dict) -> None:
    """Guarda varios filtros de una vez."""
    for key, value in cfg.items():
        set_filter(key, value)


def save_preset(name: str, config: dict) -> None:
    """Guarda (o reemplaza) un preset con nombre."""
    with _conn() as c:
        c.execute(
            "INSERT INTO presets(name, config) VALUES(?, ?) "
            "ON CONFLICT(name) DO UPDATE SET config=excluded.config",
            (name, json.dumps(config)),
        )


def list_presets() -> list:
    """Lista los presets guardados: [(id, name, config_dict), ...]."""
    with _conn() as c:
        return [
            (row[0], row[1], json.loads(row[2]))
            for row in c.execute(
                "SELECT id, name, config FROM presets ORDER BY name"
            )
        ]


def delete_preset(preset_id: int) -> None:
    with _conn() as c:
        c.execute("DELETE FROM presets WHERE id=?", (preset_id,))


# ==============================================================
#  BLOCK LOG  (historial de bloques trabajados)
# ==============================================================

def add_block(date: str, station: str, pay: float, duration: float) -> None:
    """Registra un bloque trabajado."""
    from datetime import datetime
    with _conn() as c:
        c.execute(
            "INSERT INTO blocks(date, station, pay, duration, created_at) "
            "VALUES(?, ?, ?, ?, ?)",
            (date, station, pay, duration, datetime.now().isoformat(timespec="seconds")),
        )


def list_blocks() -> list:
    """Lista los bloques, mas recientes primero. Cada uno es un dict."""
    with _conn() as c:
        rows = c.execute(
            "SELECT id, date, station, pay, duration FROM blocks "
            "ORDER BY date DESC, id DESC"
        ).fetchall()
    out = []
    for bid, date, station, pay, duration in rows:
        ph = (pay / duration) if duration else 0.0
        out.append({
            "id": bid, "date": date, "station": station,
            "pay": pay, "duration": duration, "pay_hour": ph,
        })
    return out


def delete_block(block_id: int) -> None:
    with _conn() as c:
        c.execute("DELETE FROM blocks WHERE id=?", (block_id,))


def dashboard_stats() -> dict:
    """Calcula las metricas del Dashboard a partir de los bloques."""
    from datetime import datetime
    blocks = list_blocks()
    stats = {
        "avg_pay_hour": 0.0,
        "count_month": 0,
        "total_earnings": 0.0,
        "best_station": "-",
    }
    if not blocks:
        return stats

    # $/hora promedio (de bloques con duracion > 0)
    rates = [b["pay_hour"] for b in blocks if b["duration"]]
    if rates:
        stats["avg_pay_hour"] = sum(rates) / len(rates)

    # Ganancia total
    stats["total_earnings"] = sum(b["pay"] for b in blocks)

    # Bloques del mes actual
    ym = datetime.now().strftime("%Y-%m")
    stats["count_month"] = sum(1 for b in blocks if str(b["date"]).startswith(ym))

    # Mejor estacion por $/hora promedio
    by_station = {}
    for b in blocks:
        if b["duration"]:
            by_station.setdefault(b["station"], []).append(b["pay_hour"])
    if by_station:
        best = max(by_station.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
        stats["best_station"] = best[0] or "-"

    return stats


def export_blocks_csv(path: str) -> int:
    """Exporta los bloques a un CSV. Devuelve cuantas filas escribio."""
    import csv
    blocks = list_blocks()
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["fecha", "estacion", "pago", "duracion_horas", "pago_por_hora"])
        for b in blocks:
            writer.writerow([
                b["date"], b["station"], f"{b['pay']:.2f}",
                f"{b['duration']:g}", f"{b['pay_hour']:.2f}",
            ])
    return len(blocks)
