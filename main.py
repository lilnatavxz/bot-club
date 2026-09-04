import os
import sqlite3
import discord
from discord.ext import commands
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================
PREFIJO = "r!"
COLOR_CLUB = discord.Color.blue()  # Cambiá esto por el color de tu club

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIJO, intents=intents, help_command=None)

# ============================================
# BASE DE DATOS (SQLite)
# ============================================
conn = sqlite3.connect("club.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS jugadores (
    discord_id INTEGER PRIMARY KEY,
    discord_name TEXT,
    nombre_club TEXT,
    posicion TEXT,
    estado TEXT DEFAULT 'activo'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS partidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rival TEXT,
    fecha TEXT,
    competicion TEXT,
    localia TEXT,
    resultado TEXT DEFAULT 'Pendiente'
)
""")
conn.commit()

# ============================================
# EVENTOS
# ============================================
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    print(f"Prefijo: {PREFIJO}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tenés permisos para usar este comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Falta un dato. Usá `r!ayuda` para ver cómo se usa el comando.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # ignoramos comandos que no existen
    else:
        await ctx.send(f"❌ Ocurrió un error: `{error}`")
        print(f"Error: {error}")


# ============================================
# COMANDOS: JUGADORES
# ============================================
@bot.command(name="registro")
@commands.has_permissions(manage_guild=True)
async def registro(ctx, usuario: discord.Member, nombre_club: str, posicion: str = "Sin definir"):
    """Registra un jugador en el club. Uso: r!registro @usuario NombreClub [Posicion]"""
    cursor.execute(
        "INSERT OR REPLACE INTO jugadores (discord_id, discord_name, nombre_club, posicion, estado) VALUES (?, ?, ?, ?, 'activo')",
        (usuario.id, str(usuario), nombre_club, posicion)
    )
    conn.commit()

    embed = discord.Embed(
        title="✅ Jugador registrado correctamente",
        color=COLOR_CLUB
    )
    embed.add_field(name="Discord", value=usuario.mention, inline=True)
    embed.add_field(name="Nombre en el club", value=nombre_club, inline=True)
    embed.add_field(name="Posición", value=posicion, inline=True)
    await ctx.send(embed=embed)


@bot.command(name="baja")
@commands.has_permissions(manage_guild=True)
async def baja(ctx, usuario: discord.Member):
    """Marca a un jugador como inactivo. Uso: r!baja @usuario"""
    cursor.execute("SELECT * FROM jugadores WHERE discord_id = ?", (usuario.id,))
    if not cursor.fetchone():
        await ctx.send("❌ Ese usuario no está registrado como jugador.")
        return

    cursor.execute("UPDATE jugadores SET estado = 'inactivo' WHERE discord_id = ?", (usuario.id,))
    conn.commit()
    await ctx.send(f"✅ {usuario.mention} fue marcado como **inactivo**.")


@bot.command(name="jugadores")
async def jugadores(ctx):
    """Muestra todos los jugadores registrados."""
    cursor.execute("SELECT discord_name, nombre_club, posicion, estado FROM jugadores")
    filas = cursor.fetchall()

    if not filas:
        await ctx.send("ℹ️ Todavía no hay jugadores registrados. Usá `r!registro`.")
        return

    embed = discord.Embed(title="📋 Jugadores del club", color=COLOR_CLUB)
    for discord_name, nombre_club, posicion, estado in filas:
        icono = "🟢" if estado == "activo" else "🔴"
        embed.add_field(
            name=f"{icono} {nombre_club}",
            value=f"Discord: {discord_name}\nPosición: {posicion}",
            inline=False
        )
    await ctx.send(embed=embed)


@bot.command(name="plantilla")
async def plantilla(ctx, posicion: str = None):
    """Muestra la plantilla completa, opcionalmente filtrada por posición. Uso: r!plantilla [posicion]"""
    if posicion:
        cursor.execute(
            "SELECT nombre_club, discord_name FROM jugadores WHERE estado = 'activo' AND LOWER(posicion) = LOWER(?)",
            (posicion,)
        )
    else:
        cursor.execute("SELECT nombre_club, discord_name, posicion FROM jugadores WHERE estado = 'activo'")

    filas = cursor.fetchall()
    if not filas:
        await ctx.send("ℹ️ No hay jugadores activos para mostrar.")
        return

    titulo = f"📋 Plantilla — {posicion.title()}" if posicion else "📋 Plantilla completa"
    embed = discord.Embed(title=titulo, color=COLOR_CLUB)

    if posicion:
        texto = "\n".join([f"• {nombre} ({discord_name})" for nombre, discord_name in filas])
        embed.description = texto
    else:
        # Agrupar por posición
        posiciones = {}
        for nombre, discord_name, pos in filas:
            posiciones.setdefault(pos, []).append(f"• {nombre} ({discord_name})")
        for pos, jugadores_list in posiciones.items():
            embed.add_field(name=pos, value="\n".join(jugadores_list), inline=False)

    await ctx.send(embed=embed)


# ============================================
# COMANDOS: PARTIDOS
# ============================================
@bot.group(name="partido", invoke_without_command=True)
async def partido(ctx):
    """Grupo de comandos de partidos. Usá r!ayuda para ver las opciones."""
    await ctx.send("ℹ️ Usá: `r!partido crear`, `r!partido resultado`, `r!partido info` o `r!partido lista`")


@partido.command(name="crear")
@commands.has_permissions(manage_guild=True)
async def partido_crear(ctx, rival: str, fecha: str, competicion: str, localia: str):
    """Crea un partido. Uso: r!partido crear Rival "DD/MM/YYYY HH:MM" Competicion Local/Visitante"""
    if localia.lower() not in ["local", "visitante"]:
        await ctx.send("❌ La localía debe ser `local` o `visitante`.")
        return

    cursor.execute(
        "INSERT INTO partidos (rival, fecha, competicion, localia) VALUES (?, ?, ?, ?)",
        (rival, fecha, competicion, localia.lower())
    )
    conn.commit()
    partido_id = cursor.lastrowid

    embed = discord.Embed(title="✅ Partido creado", color=COLOR_CLUB)
    embed.add_field(name="ID", value=str(partido_id), inline=True)
    embed.add_field(name="Rival", value=rival, inline=True)
    embed.add_field(name="Fecha", value=fecha, inline=True)
    embed.add_field(name="Competición", value=competicion, inline=True)
    embed.add_field(name="Condición", value=localia.title(), inline=True)
    await ctx.send(embed=embed)


@partido.command(name="resultado")
@commands.has_permissions(manage_guild=True)
async def partido_resultado(ctx, partido_id: int, *, resultado: str):
    """Registra o actualiza el resultado de un partido. Uso: r!partido resultado ID 2-1"""
    cursor.execute("SELECT * FROM partidos WHERE id = ?", (partido_id,))
    if not cursor.fetchone():
        await ctx.send("❌ No existe un partido con ese ID.")
        return

    cursor.execute("UPDATE partidos SET resultado = ? WHERE id = ?", (resultado, partido_id))
    conn.commit()
    await ctx.send(f"✅ Resultado del partido #{partido_id} actualizado: **{resultado}**")


@partido.command(name="info")
async def partido_info(ctx, partido_id: int):
    """Muestra la información de un partido. Uso: r!partido info ID"""
    cursor.execute("SELECT rival, fecha, competicion, localia, resultado FROM partidos WHERE id = ?", (partido_id,))
    fila = cursor.fetchone()
    if not fila:
        await ctx.send("❌ No existe un partido con ese ID.")
        return

    rival, fecha, competicion, localia, resultado = fila
    embed = discord.Embed(title=f"⚽ Partido #{partido_id}", color=COLOR_CLUB)
    embed.add_field(name="Rival", value=rival, inline=True)
    embed.add_field(name="Fecha", value=fecha, inline=True)
    embed.add_field(name="Competición", value=competicion, inline=True)
    embed.add_field(name="Condición", value=localia.title(), inline=True)
    embed.add_field(name="Resultado", value=resultado, inline=True)
    await ctx.send(embed=embed)


@partido.command(name="lista")
async def partido_lista(ctx):
    """Muestra todos los partidos registrados."""
    cursor.execute("SELECT id, rival, fecha, resultado FROM partidos ORDER BY id DESC LIMIT 15")
    filas = cursor.fetchall()
    if not filas:
        await ctx.send("ℹ️ Todavía no hay partidos registrados. Usá `r!partido crear`.")
        return

    embed = discord.Embed(title="📅 Partidos", color=COLOR_CLUB)
    for pid, rival, fecha, resultado in filas:
        embed.add_field(
            name=f"#{pid} vs {rival}",
            value=f"{fecha} — {resultado}",
            inline=False
        )
    await ctx.send(embed=embed)


# ============================================
# AYUDA
# ============================================
@bot.command(name="ayuda")
async def ayuda(ctx):
    embed = discord.Embed(title="📖 Comandos disponibles", color=COLOR_CLUB)
    embed.add_field(
        name="Jugadores",
        value=(
            "`r!registro @usuario NombreClub [Posicion]` — registrar jugador (staff)\n"
            "`r!baja @usuario` — marcar inactivo (staff)\n"
            "`r!jugadores` — ver todos los jugadores\n"
            "`r!plantilla [posicion]` — ver plantilla"
        ),
        inline=False
    )
    embed.add_field(
        name="Partidos",
        value=(
            "`r!partido crear Rival Fecha Competicion Local/Visitante` (staff)\n"
            "`r!partido resultado ID 2-1` (staff)\n"
            "`r!partido info ID`\n"
            "`r!partido lista`"
        ),
        inline=False
    )
    await ctx.send(embed=embed)


# ============================================
# INICIO DEL BOT
# ============================================
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
