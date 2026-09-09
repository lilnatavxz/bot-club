import os
import asyncio
import discord
from discord.ext import commands

PREFIJO = "r!"
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIJO, intents=intents, help_command=None)

COGS = [
    "cogs.plantillas",
]


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"❌ Ocurrió un error: `{error}`")
        print(f"Error: {error}")


@bot.command(name="ayuda")
async def ayuda(ctx):
    embed = discord.Embed(title="📖 Comandos disponibles", color=discord.Color.gold())
    embed.add_field(
        name="Comunicados",
        value=(
            "`r!plantilla1` — genera un comunicado con la plantilla del Real Madrid\n"
            "`r!plantillas` — ver todas las plantillas disponibles"
        ),
        inline=False
    )
    await ctx.send(embed=embed)


async def main():
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
