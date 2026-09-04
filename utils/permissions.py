from database import db


def es_staff(member) -> bool:
    """Devuelve True si el usuario es administrador de Discord o tiene el rol staff configurado."""
    if member.guild_permissions.administrator:
        return True

    config = db.obtener_config(member.guild.id)
    staff_role_id = config["staff_role_id"]
    if not staff_role_id:
        return False

    return any(role.id == staff_role_id for role in member.roles)


def solo_staff():
    """Decorador para comandos que requieren rol de staff configurado."""
    from discord.ext import commands

    async def predicate(ctx):
        if es_staff(ctx.author):
            return True
        await ctx.send("❌ No tienes permisos para utilizar este comando.")
        return False

    return commands.check(predicate)
  
