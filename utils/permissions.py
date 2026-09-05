import discord
from discord.ext import commands


def es_encargado(member) -> bool:
    """Devuelve True si el usuario es administrador de Discord o tiene el rol 'Encargados'."""
    if member.guild_permissions.administrator:
        return True

    rol = discord.utils.get(member.guild.roles, name="Encargados")
    if not rol:
        return False

    return rol in member.roles


def solo_encargados():
    """Decorador para comandos que requieren el rol Encargados (o ser administrador)."""
    async def predicate(ctx):
        if es_encargado(ctx.author):
            return True
        await ctx.send("❌ No tienes permisos para utilizar este comando.")
        return False

    return commands.check(predicate)
