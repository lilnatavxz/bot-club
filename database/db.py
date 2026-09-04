import sqlite3
from datetime import datetime

conn = sqlite3.connect("club.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


def inicializar():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jugadores (
        discord_id INTEGER PRIMARY KEY,
        guild_id INTEGER,
        discord_name TEXT,
        alias TEXT,
        numero TEXT,
        posicion_principal TEXT,
        posiciones_secundarias TEXT,
        posicion_actual TEXT,
        rango TEXT DEFAULT 'Sin rango',
        estado TEXT DEFAULT 'Activo',
        goles INTEGER DEFAULT 0,
        asistencias INTEGER DEFAULT 0,
        partidos INTEGER DEFAULT 0,
        fecha_registro TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config_servidor (
        guild_id INTEGER PRIMARY KEY,
        staff_role_id INTEGER,
        canal_registros INTEGER,
        canal_partidos INTEGER,
        canal_convocatorias INTEGER,
        canal_logs INTEGER,
        formacion_predeterminada TEXT,
        estado_predeterminado TEXT DEFAULT 'Activo'
    )
    """)
    conn.commit()


# ---------- JUGADORES ----------
def registrar_jugador(discord_id, guild_id, discord_name, alias, posicion_principal, posiciones_secundarias, rango):
    cursor.execute(
        """INSERT OR REPLACE INTO jugadores
        (discord_id, guild_id, discord_name, alias, posicion_principal, posiciones_secundarias,
         posicion_actual, rango, estado, fecha_registro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Activo', ?)""",
        (discord_id, guild_id, discord_name, alias, posicion_principal, posiciones_secundarias,
         posicion_principal, rango, datetime.now().strftime("%d/%m/%Y"))
    )
    conn.commit()


def obtener_jugador(discord_id):
    cursor.execute("SELECT * FROM jugadores WHERE discord_id = ?", (discord_id,))
    return cursor.fetchone()


def obtener_jugadores(guild_id):
    cursor.execute("SELECT * FROM jugadores WHERE guild_id = ? ORDER BY alias", (guild_id,))
    return cursor.fetchall()


def actualizar_campo_jugador(discord_id, campo, valor):
    campos_permitidos = [
        "alias", "posicion_principal", "posiciones_secundarias",
        "posicion_actual", "rango", "estado", "numero"
    ]
    if campo not in campos_permitidos:
        raise ValueError("Campo no permitido")
    cursor.execute(f"UPDATE jugadores SET {campo} = ? WHERE discord_id = ?", (valor, discord_id))
    conn.commit()


def eliminar_jugador(discord_id):
    cursor.execute("DELETE FROM jugadores WHERE discord_id = ?", (discord_id,))
    conn.commit()


# ---------- CONFIGURACIÓN DE SERVIDOR ----------
def obtener_config(guild_id):
    cursor.execute("SELECT * FROM config_servidor WHERE guild_id = ?", (guild_id,))
    fila = cursor.fetchone()
    if not fila:
        cursor.execute("INSERT INTO config_servidor (guild_id) VALUES (?)", (guild_id,))
        conn.commit()
        cursor.execute("SELECT * FROM config_servidor WHERE guild_id = ?", (guild_id,))
        fila = cursor.fetchone()
    return fila


def actualizar_config(guild_id, campo, valor):
    campos_permitidos = [
        "staff_role_id", "canal_registros", "canal_partidos",
        "canal_convocatorias", "canal_logs", "formacion_predeterminada", "estado_predeterminado"
    ]
    if campo not in campos_permitidos:
        raise ValueError("Campo no permitido")
    obtener_config(guild_id)  # asegura que exista la fila
    cursor.execute(f"UPDATE config_servidor SET {campo} = ? WHERE guild_id = ?", (valor, guild_id))
    conn.commit()
  
