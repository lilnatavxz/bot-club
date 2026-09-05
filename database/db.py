import sqlite3
from datetime import datetime

conn = sqlite3.connect("club.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


def inicializar():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS partidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        imagen_blob BLOB,
        imagen_filename TEXT,
        creado_por INTEGER,
        estado TEXT DEFAULT 'Programado',
        fecha_creacion TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS convocatoria (
        partido_id INTEGER,
        discord_id INTEGER,
        respuesta TEXT DEFAULT 'Pendiente',
        PRIMARY KEY (partido_id, discord_id)
    )
    """)
    conn.commit()


# ---------- PARTIDOS ----------
def crear_partido(guild_id, imagen_blob, imagen_filename, creado_por):
    cursor.execute(
        """INSERT INTO partidos (guild_id, imagen_blob, imagen_filename, creado_por, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)""",
        (guild_id, imagen_blob, imagen_filename, creado_por, datetime.now().strftime("%d/%m/%Y %H:%M"))
    )
    conn.commit()
    return cursor.lastrowid


def obtener_partido(partido_id):
    cursor.execute("SELECT * FROM partidos WHERE id = ?", (partido_id,))
    return cursor.fetchone()


def obtener_proximo_partido(guild_id):
    cursor.execute(
        "SELECT * FROM partidos WHERE guild_id = ? AND estado = 'Programado' ORDER BY id DESC LIMIT 1",
        (guild_id,)
    )
    return cursor.fetchone()


def actualizar_estado_partido(partido_id, estado):
    cursor.execute("UPDATE partidos SET estado = ? WHERE id = ?", (estado, partido_id))
    conn.commit()


# ---------- CONVOCATORIA ----------
def responder_convocatoria(partido_id, discord_id, respuesta):
    cursor.execute(
        "INSERT OR REPLACE INTO convocatoria (partido_id, discord_id, respuesta) VALUES (?, ?, ?)",
        (partido_id, discord_id, respuesta)
    )
    conn.commit()


def obtener_convocatoria(partido_id):
    cursor.execute("SELECT discord_id, respuesta FROM convocatoria WHERE partido_id = ?", (partido_id,))
    return cursor.fetchall()
