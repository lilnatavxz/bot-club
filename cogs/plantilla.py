import discord
from discord.ext import commands
from database import db
from utils.embeds import embed_error, embed_exito
from utils.permissions import solo_staff
from config.settings import COLOR_CLUB

ICONOS_GRUPO = {
    "GK": "🧤",
    "DFC": "🛡️", "LD": "🛡️", "LI": "🛡️",
    "MCD": "⚙️", "MC": "⚙️", "MCO": "⚙️", "MD": "⚙️", "MI": "⚙️",
    "DC": "⚡",
}

NOMBRES_GRUPO = {
    "🧤": "PORTEROS",
    "🛡️": "DEFENSAS",
    "⚙️": "MEDIOCAMPISTAS",
    "⚡": "DELANTEROS",
}


class PlantillaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="plantilla")
    async def plantilla(self, ctx):
        """Muestra la plantilla actual en formato visual, agrupada por posición."""
        jugadores = db.obtener_jugadores(ctx.guild.id)
        activos = [j for j in jugadores if j["estado"] == "Activo"]

        if not activos:
            await ctx.send(embed=embed_error("Todavía no hay jugadores activos en la plantilla."))
            return

        grupos = {"🧤": [], "🛡️": [], "⚙️": [], "⚡": []}
        for j in activos:
            icono = ICONOS_GRUPO.get(j["posicion_actual"], "⚙️")
            grupos[icono].append(j["alias"])

        texto = "⚽ **PLANTILLA**\n\n"
        for icono, nombres in grupos.items():
            if not nombres:
                continue
            texto += f"{icono} {NOMBRES_GRUPO[icono]}\n"
            for nombre in nombres:
                texto += f"└ {nombre}\n"
            texto += "\n"

        embed = discord.Embed(description=texto, color=COLOR_CLUB)
        await ctx.send(embed=embed)

    @commands.command(name="formacion")
    async def formacion(self, ctx, *, nueva_formacion: str = None):
        """Muestra la formación actual, o la cambia si sos staff. Uso: r!formacion [4-3-3]"""
        conf = db.obtener_config(ctx.guild.id)

        if nueva_formacion is None:
            actual = conf["formacion_predeterminada"] or "No configurada"
            await ctx.send(embed=discord.Embed(
                title="📐 Formación actual",
                description=f"**{actual}**",
                color=COLOR_CLUB
            ))
            return

        from utils.permissions import es_staff
        if not es_staff(ctx.author):
            await ctx.send(embed=embed_error("Solo el staff puede cambiar la formación."))
            return

        db.actualizar_config(ctx.guild.id, "formacion_predeterminada", nueva_formacion)
        await ctx.send(embed=embed_exito(f"Formación actualizada a **{nueva_formacion}**"))


async def setup(bot):
    await bot.add_cog(PlantillaCog(bot))
