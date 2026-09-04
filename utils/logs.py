import discord
from datetime import datetime
from database import db


async def registrar_log(bot, guild, usuario_staff, accion, jugador_texto=None, cambio=None):
    """Envía un embed de log al canal configurado, si existe."""
    conf = db.obtener_config(guild.id)
    canal_id = conf["canal_logs"]
    if not canal_id:
        return

    canal = guild.get_channel(canal_id)
    if not canal:
        return

    embed = discord.Embed(title="📋 Registro de actividad", color=discord.Color.dark_grey())
    embed.add_field(name="Usuario", value=usuario_staff.mention, inline=True)
    embed.add_field(name="Acción", value=accion, inline=True)
    if jugador_texto:
        embed.add_field(name="Jugador", value=jugador_texto, inline=True)
    if cambio:
        embed.add_field(name="Cambio", value=cambio, inline=False)
    embed.set_footer(text=datetime.now().strftime("%d/%m/%Y %H:%M"))

    try:
        await canal.send(embed=embed)
    except discord.Forbidden:
        pass  # el bot no tiene permiso en ese canal, no rompemos el flujo principal
