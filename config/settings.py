import os

# Prefijo de comandos
PREFIJO = "r!"

# Color usado en todos los embeds (cambialo por el color de tu club)
COLOR_CLUB = 0x2b6cb0

# Token del bot (se configura como variable de entorno en Railway, NUNCA en el código)
TOKEN = os.getenv("DISCORD_TOKEN")

# Estados válidos para un jugador
ESTADOS_VALIDOS = ["Activo", "Inactivo", "Ausente"]

# Posiciones válidas (podés ampliar esta lista)
POSICIONES_VALIDAS = ["GK", "DFC", "LD", "LI", "MCD", "MC", "MCO", "MD", "MI", "DC"]
