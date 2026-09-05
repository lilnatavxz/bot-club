import discord


def embed_error(mensaje: str) -> discord.Embed:
    return discord.Embed(description=f"❌ {mensaje}", color=discord.Color.red())


def embed_exito(mensaje: str) -> discord.Embed:
    return discord.Embed(description=f"✅ {mensaje}", color=discord.Color.green())
