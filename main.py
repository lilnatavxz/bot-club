import asyncio
import discord
from discord.ext import commands

from config.settings import PREFIJO, TOKEN
from database import db

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIJO, intents=intents, help_command=None)

COGS = [
    "cogs.jugador",
    "cogs.staff",
    "cogs.config_cmds",
    "cogs.partidos",
    "cogs.plantilla",
    "cogs.stats",
]


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    print(f"Prefijo: {PREFIJO}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        pass  # el mensaje de error ya lo manda el check (solo_staff, etc.)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Falta un dato. Usá `r!ayuda` para ver cómo se usa el comando.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ No encontré a ese usuario. Mencionalo con @.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"❌ Ocurrió un error: `{error}`")
        print(f"Error: {error}")


@bot.command(name="ayuda")
async def ayuda(ctx):
    embed = discord.Embed(title="📖 Comandos disponibles", color=discord.Color.blue())
    embed.add_field(
        name="👤 Jugadores",
        value="`r!yo` `r!perfil @usuario` `r!posiciones` `r!jugadores` `r!buscar <nombre>`",
        inline=False
    )
    embed.add_field(
        name="⚽ Partidos",
        value="`r!partido` `r!convocatoria` `r!plantilla` `r!formacion`",
        inline=False
    )
    embed.add_field(
        name="📊 Estadísticas",
        value="`r!stats` `r!stats @usuario`",
        inline=False
    )
    embed.add_field(
        name="🔒 Staff",
        value=(
            "`r!registrar @usuario` `r!editar @usuario` `r!eliminar @usuario` "
            "`r!rango` `r!estado` `r!gol` `r!asistencia`\n"
            "`r!partido crear` `r!partido capitan` `r!partido finalizar`"
        ),
        inline=False
    )
    embed.add_field(
        name="🔒 Administración",
        value="`r!config` (ver todas las opciones con `r!config`)",
        inline=False
    )
    await ctx.send(embed=embed)


async def main():
    db.inicializar()
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
