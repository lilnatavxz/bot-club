import discord
from discord.ext import commands

from generador import generar_comunicado

PLANTILLAS = {
    "plantilla1": {
        "nombre": "Real Madrid",
        "comando": "plantilla1",
    }
}


class PlantillasCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="plantilla1")
    async def plantilla1(self, ctx):
        """Genera un comunicado con la plantilla del Real Madrid, paso a paso."""

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        await ctx.send("📝 Escribe el título del comunicado:")
        try:
            msg_titulo = await self.bot.wait_for("message", check=check, timeout=120)
        except TimeoutError:
            await ctx.send("❌ Se acabó el tiempo. Volvé a usar `r!plantilla1` para intentarlo de nuevo.")
            return
        titulo = msg_titulo.content

        await ctx.send("📄 Escribe el contenido del comunicado:")
        try:
            msg_contenido = await self.bot.wait_for("message", check=check, timeout=180)
        except TimeoutError:
            await ctx.send("❌ Se acabó el tiempo. Volvé a usar `r!plantilla1` para intentarlo de nuevo.")
            return
        contenido = msg_contenido.content

        async with ctx.typing():
            imagen = generar_comunicado(titulo, contenido)
            ruta_temp = f"/tmp/comunicado_{ctx.message.id}.png"
            imagen.save(ruta_temp)

        await ctx.send(file=discord.File(ruta_temp, filename="comunicado.png"))

    @commands.command(name="plantillas")
    async def plantillas(self, ctx):
        """Muestra todas las plantillas disponibles."""
        embed = discord.Embed(title="🖼️ Plantillas disponibles", color=discord.Color.gold())
        for datos in PLANTILLAS.values():
            embed.add_field(
                name=f"r!{datos['comando']}",
                value=f"Comunicado estilo **{datos['nombre']}**",
                inline=False
            )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PlantillasCog(bot))
  
