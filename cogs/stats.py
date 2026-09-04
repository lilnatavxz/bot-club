import discord
from discord.ext import commands
from database import db
from utils.embeds import embed_error
from utils.permissions import solo_staff
from config.settings import COLOR_CLUB


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stats")
    async def stats(self, ctx, usuario: discord.Member = None):
        """Muestra estadísticas generales del club, o individuales si mencionás a alguien."""
        if usuario:
            jugador = db.obtener_jugador(usuario.id)
            if not jugador:
                await ctx.send(embed=embed_error("Ese usuario no está registrado."))
                return

            embed = discord.Embed(title=f"📊 Estadísticas de {jugador['alias']}", color=COLOR_CLUB)
            embed.add_field(name="Partidos", value=str(jugador["partidos"]), inline=True)
            embed.add_field(name="Goles", value=str(jugador["goles"]), inline=True)
            embed.add_field(name="Asistencias", value=str(jugador["asistencias"]), inline=True)
            embed.add_field(name="Posición utilizada", value=jugador["posicion_actual"] or "—", inline=True)
            await ctx.send(embed=embed)
            return

        datos = db.contar_stats_generales(ctx.guild.id)
        embed = discord.Embed(title="📊 Estadísticas del club", color=COLOR_CLUB)
        embed.add_field(name="Jugadores registrados", value=str(datos["total_jugadores"]), inline=True)
        embed.add_field(name="Activos", value=str(datos["por_estado"].get("Activo", 0)), inline=True)
        embed.add_field(name="Inactivos", value=str(datos["por_estado"].get("Inactivo", 0)), inline=True)
        embed.add_field(name="Ausentes", value=str(datos["por_estado"].get("Ausente", 0)), inline=True)
        embed.add_field(name="Partidos registrados", value=str(datos["total_partidos"]), inline=True)

        if datos["por_posicion"]:
            texto_posiciones = "\n".join([f"{pos or 'Sin definir'}: {cant}" for pos, cant in datos["por_posicion"].items()])
            embed.add_field(name="Jugadores por posición", value=texto_posiciones, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="gol")
    @solo_staff()
    async def gol(self, ctx, usuario: discord.Member, cantidad: int = 1):
        """Suma goles a un jugador. Uso: r!gol @usuario [cantidad]"""
        jugador = db.obtener_jugador(usuario.id)
        if not jugador:
            await ctx.send(embed=embed_error("Ese usuario no está registrado."))
            return
        db.sumar_stat_jugador(usuario.id, "goles", cantidad)
        await ctx.send(f"⚽ {jugador['alias']} ahora tiene **{jugador['goles'] + cantidad}** goles.")

    @commands.command(name="asistencia")
    @solo_staff()
    async def asistencia(self, ctx, usuario: discord.Member, cantidad: int = 1):
        """Suma asistencias a un jugador. Uso: r!asistencia @usuario [cantidad]"""
        jugador = db.obtener_jugador(usuario.id)
        if not jugador:
            await ctx.send(embed=embed_error("Ese usuario no está registrado."))
            return
        db.sumar_stat_jugador(usuario.id, "asistencias", cantidad)
        await ctx.send(f"🎯 {jugador['alias']} ahora tiene **{jugador['asistencias'] + cantidad}** asistencias.")

    @commands.command(name="buscar")
    async def buscar(self, ctx, *, nombre: str):
        """Busca jugadores registrados por alias. Uso: r!buscar nombre"""
        jugadores = db.obtener_jugadores(ctx.guild.id)
        coincidencias = [j for j in jugadores if nombre.lower() in (j["alias"] or "").lower()]

        if not coincidencias:
            await ctx.send(embed=embed_error(f"No encontré jugadores que coincidan con \"{nombre}\"."))
            return

        embed = discord.Embed(title=f"🔎 Resultados para \"{nombre}\"", color=COLOR_CLUB)
        for j in coincidencias[:10]:
            embed.add_field(
                name=j["alias"],
                value=f"Posición: {j['posicion_actual']} | Estado: {j['estado']}",
                inline=False
            )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(StatsCog(bot))
  
