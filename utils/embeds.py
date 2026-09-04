import discord
from config.settings import COLOR_CLUB


def embed_error(mensaje: str) -> discord.Embed:
    return discord.Embed(description=f"❌ {mensaje}", color=discord.Color.red())


def embed_exito(mensaje: str) -> discord.Embed:
    return discord.Embed(description=f"✅ {mensaje}", color=discord.Color.green())


def embed_perfil(jugador, es_propio: bool = False) -> discord.Embed:
    titulo = "⚽ Mi perfil" if es_propio else f"⚽ Perfil de {jugador['alias']}"
    embed = discord.Embed(title=titulo, color=COLOR_CLUB)
    embed.add_field(name="Alias", value=jugador["alias"] or "—", inline=True)
    embed.add_field(name="Posición actual", value=jugador["posicion_actual"] or "—", inline=True)
    embed.add_field(name="Posición principal", value=jugador["posicion_principal"] or "—", inline=True)
    secundarias = jugador["posiciones_secundarias"] or "Ninguna"
    embed.add_field(name="Posiciones secundarias", value=secundarias, inline=True)
    embed.add_field(name="Rango", value=jugador["rango"] or "Sin rango", inline=True)

    icono_estado = {"Activo": "🟢", "Inactivo": "🔴", "Ausente": "🟡"}.get(jugador["estado"], "⚪")
    embed.add_field(name="Estado", value=f"{icono_estado} {jugador['estado']}", inline=True)

    if jugador["fecha_registro"]:
        embed.set_footer(text=f"Registrado el {jugador['fecha_registro']}")
    return embed
  
