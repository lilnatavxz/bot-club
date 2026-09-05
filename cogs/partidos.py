import io
import discord
from discord.ext import commands
from database import db
from utils.embeds import embed_error, embed_exito
from utils.permissions import solo_encargados
from config.settings import COLOR_CLUB


def _buscar_canal_partidos(guild):
    """Busca el canal llamado 'partidos' (el que crea r!setup_estructura dentro de Primer Equipo)."""
    return discord.utils.get(guild.text_channels, name="partidos")


def _embed_y_archivo_partido(partido, titulo="⚽ Partido"):
    archivo = discord.File(io.BytesIO(partido["imagen_blob"]), filename=partido["imagen_filename"])
    embed = discord.Embed(title=titulo, color=COLOR_CLUB)
    embed.set_image(url=f"attachment://{partido['imagen_filename']}")
    embed.set_footer(text=f"ID del partido: {partido['id']} — Estado: {partido['estado']}")
    return embed, archivo


class ConvocatoriaView(discord.ui.View):
    def __init__(self, partido_id):
        super().__init__(timeout=None)  # los botones quedan activos indefinidamente
        self.partido_id = partido_id

    async def _responder(self, interaction: discord.Interaction, respuesta: str):
        db.responder_convocatoria(self.partido_id, interaction.user.id, respuesta)
        await interaction.response.send_message(f"Registrado: **{respuesta}** ✅", ephemeral=True)

    @discord.ui.button(label="Confirmar asistencia", style=discord.ButtonStyle.success, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._responder(interaction, "Confirmado")

    @discord.ui.button(label="No disponible", style=discord.ButtonStyle.danger, emoji="❌")
    async def no_disponible(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._responder(interaction, "No disponible")


class PartidosCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="partido", invoke_without_command=True)
    async def partido(self, ctx):
        """Muestra el próximo partido programado."""
        partido = db.obtener_proximo_partido(ctx.guild.id)
        if not partido:
            await ctx.send(embed=embed_error("No hay ningún partido programado. Un Encargado puede usar `r!partido crear`."))
            return

        embed, archivo = _embed_y_archivo_partido(partido, "⚽ Próximo partido")
        await ctx.send(embed=embed, file=archivo, view=ConvocatoriaView(partido["id"]))

    @partido.command(name="crear")
    @solo_encargados()
    async def partido_crear(self, ctx):
        """Crea un partido: te pide que subas la imagen del anuncio (rival, hora, lugar)."""
        await ctx.send(
            "📸 Subí la imagen del partido (con rival, hora y lugar) en tu próximo mensaje en este canal. "
            "Tenés 2 minutos."
        )

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and len(m.attachments) > 0

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=120)
        except TimeoutError:
            await ctx.send(embed=embed_error("Se acabó el tiempo. Volvé a usar `r!partido crear` para intentarlo de nuevo."))
            return

        adjunto = msg.attachments[0]
        imagen_bytes = await adjunto.read()

        partido_id = db.crear_partido(ctx.guild.id, imagen_bytes, adjunto.filename, ctx.author.id)
        partido = db.obtener_partido(partido_id)

        embed, archivo = _embed_y_archivo_partido(partido, "⚽ Nuevo partido")
        canal_destino = _buscar_canal_partidos(ctx.guild) or ctx.channel

        await canal_destino.send(embed=embed, file=archivo, view=ConvocatoriaView(partido_id))

        if canal_destino != ctx.channel:
            await ctx.send(embed=embed_exito(f"Partido publicado en {canal_destino.mention}"))

    @partido.command(name="finalizar")
    @solo_encargados()
    async def partido_finalizar(self, ctx, partido_id: int):
        """Marca un partido como finalizado. Uso: r!partido finalizar ID"""
        partido = db.obtener_partido(partido_id)
        if not partido:
            await ctx.send(embed=embed_error("No existe un partido con ese ID."))
            return
        db.actualizar_estado_partido(partido_id, "Finalizado")
        await ctx.send(embed=embed_exito(f"Partido #{partido_id} marcado como finalizado."))

    @commands.command(name="convocatoria")
    async def convocatoria(self, ctx, partido_id: int = None):
        """Muestra quién confirmó asistencia al partido. Uso: r!convocatoria [ID]"""
        partido = db.obtener_partido(partido_id) if partido_id else db.obtener_proximo_partido(ctx.guild.id)
        if not partido:
            await ctx.send(embed=embed_error("No hay ningún partido para mostrar."))
            return

        respuestas = db.obtener_convocatoria(partido["id"])
        confirmados = [f"<@{r['discord_id']}>" for r in respuestas if r["respuesta"] == "Confirmado"]
        no_disponibles = [f"<@{r['discord_id']}>" for r in respuestas if r["respuesta"] == "No disponible"]

        embed = discord.Embed(title=f"📋 Convocatoria — partido #{partido['id']}", color=COLOR_CLUB)
        embed.add_field(name="✅ Confirmados", value="\n".join(confirmados) or "Nadie todavía", inline=False)
        embed.add_field(name="❌ No disponibles", value="\n".join(no_disponibles) or "Nadie todavía", inline=False)
        await ctx.send(embed=embed)

    @partido_crear.error
    @partido_finalizar.error
    async def partido_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            pass  # ya se avisó desde solo_encargados()
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=embed_error("Ese ID de partido no es válido."))
        else:
            await ctx.send(embed=embed_error(f"Ocurrió un error: {error}"))


async def setup(bot):
    await bot.add_cog(PartidosCog(bot))
