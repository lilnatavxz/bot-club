import discord
from discord.ext import commands
from database import db
from utils.embeds import embed_error, embed_exito
from utils.permissions import solo_staff
from utils.logs import registrar_log
from config.settings import COLOR_CLUB

ICONOS_ESTADO_RESPUESTA = {
    "Confirmado": "✅",
    "No disponible": "❌",
    "Pendiente": "⏳",
}


def _embed_partido(partido) -> discord.Embed:
    embed = discord.Embed(title=f"⚽ Próximo partido vs {partido['rival']}", color=COLOR_CLUB)
    embed.add_field(name="Fecha", value=partido["fecha"], inline=True)
    embed.add_field(name="Hora", value=partido["hora"], inline=True)
    embed.add_field(name="Tipo", value=partido["tipo"], inline=True)
    embed.add_field(name="Formación", value=partido["formacion"] or "Sin definir", inline=True)
    if partido["capitan_id"]:
        embed.add_field(name="Capitán", value=f"<@{partido['capitan_id']}>", inline=True)
    embed.add_field(name="Estado", value=partido["estado"], inline=True)
    embed.set_footer(text=f"ID del partido: {partido['id']}")
    return embed


class ConvocatoriaView(discord.ui.View):
    def __init__(self, partido_id):
        super().__init__(timeout=None)  # los botones de asistencia quedan activos indefinidamente
        self.partido_id = partido_id

    async def _responder(self, interaction: discord.Interaction, respuesta: str):
        jugador = db.obtener_jugador(interaction.user.id)
        if not jugador:
            await interaction.response.send_message(
                "❌ No estás registrado como jugador, no podés confirmar asistencia.", ephemeral=True
            )
            return

        db.responder_convocatoria(self.partido_id, interaction.user.id, respuesta)
        await interaction.response.send_message(f"Registrado: **{respuesta}** ✅", ephemeral=True)

    @discord.ui.button(label="Confirmar asistencia", style=discord.ButtonStyle.success, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._responder(interaction, "Confirmado")

    @discord.ui.button(label="No disponible", style=discord.ButtonStyle.danger, emoji="❌")
    async def no_disponible(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._responder(interaction, "No disponible")

    @discord.ui.button(label="Cambiar posición", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def cambiar_posicion(self, interaction: discord.Interaction, button: discord.ui.Button):
        jugador = db.obtener_jugador(interaction.user.id)
        if not jugador:
            await interaction.response.send_message("❌ No estás registrado.", ephemeral=True)
            return

        from cogs.jugador import MenuPosiciones
        opciones = [jugador["posicion_principal"]]
        if jugador["posiciones_secundarias"]:
            opciones += [p.strip() for p in jugador["posiciones_secundarias"].split(",") if p.strip()]
        opciones = list(dict.fromkeys(opciones))

        await interaction.response.send_message(
            "Elegí tu posición para este partido:", view=MenuPosiciones(interaction.user.id, opciones), ephemeral=True
        )


class PartidosCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="partido", invoke_without_command=True)
    async def partido(self, ctx):
        """Muestra la información del próximo partido programado."""
        partido = db.obtener_proximo_partido(ctx.guild.id)
        if not partido:
            await ctx.send(embed=embed_error("No hay ningún partido programado. Un staff puede usar `r!partido crear`."))
            return
        await ctx.send(embed=_embed_partido(partido), view=ConvocatoriaView(partido["id"]))

    @partido.command(name="crear")
    @solo_staff()
    async def partido_crear(self, ctx, rival: str, fecha: str, hora: str, tipo: str, *, formacion: str = None):
        """Crea un partido. Uso: r!partido crear Rival Fecha Hora Tipo [Formacion]"""
        conf = db.obtener_config(ctx.guild.id)
        formacion_final = formacion or conf["formacion_predeterminada"]

        partido_id = db.crear_partido(ctx.guild.id, rival, fecha, hora, tipo, formacion_final, None)
        partido = db.obtener_partido(partido_id)

        embed = _embed_partido(partido)
        view = ConvocatoriaView(partido_id)

        conf = db.obtener_config(ctx.guild.id)
        canal_destino = ctx.channel
        if conf["canal_partidos"]:
            canal_configurado = ctx.guild.get_channel(conf["canal_partidos"])
            if canal_configurado:
                canal_destino = canal_configurado

        await canal_destino.send(embed=embed, view=view)
        if canal_destino != ctx.channel:
            await ctx.send(embed=embed_exito(f"Partido creado y publicado en {canal_destino.mention}"))

        await registrar_log(self.bot, ctx.guild, ctx.author, "Creó partido", f"vs {rival}", f"{fecha} {hora}")

    @partido.command(name="capitan")
    @solo_staff()
    async def partido_capitan(self, ctx, partido_id: int, capitan: discord.Member):
        """Asigna el capitán de un partido. Uso: r!partido capitan ID @usuario"""
        partido = db.obtener_partido(partido_id)
        if not partido:
            await ctx.send(embed=embed_error("No existe un partido con ese ID."))
            return
        db.asignar_capitan(partido_id, capitan.id)
        await ctx.send(embed=embed_exito(f"{capitan.mention} es el capitán del partido #{partido_id}."))

    @partido.command(name="finalizar")
    @solo_staff()
    async def partido_finalizar(self, ctx, partido_id: int):
        """Marca un partido como finalizado. Uso: r!partido finalizar ID"""
        partido = db.obtener_partido(partido_id)
        if not partido:
            await ctx.send(embed=embed_error("No existe un partido con ese ID."))
            return
        db.actualizar_estado_partido(partido_id, "Finalizado")
        await ctx.send(embed=embed_exito(f"Partido #{partido_id} marcado como finalizado."))
        await registrar_log(self.bot, ctx.guild, ctx.author, "Finalizó partido", f"vs {partido['rival']}")

    @commands.command(name="convocatoria")
    async def convocatoria(self, ctx, partido_id: int = None):
        """Muestra la convocatoria de un partido, separada por posición. Uso: r!convocatoria [ID]"""
        if partido_id:
            partido = db.obtener_partido(partido_id)
        else:
            partido = db.obtener_proximo_partido(ctx.guild.id)

        if not partido:
            await ctx.send(embed=embed_error("No hay ningún partido para mostrar."))
            return

        respuestas = db.obtener_convocatoria(partido["id"])

        grupos = {"🧤": [], "🛡️": [], "⚙️": [], "⚡": []}
        iconos_pos = {
            "GK": "🧤", "DFC": "🛡️", "LD": "🛡️", "LI": "🛡️",
            "MCD": "⚙️", "MC": "⚙️", "MCO": "⚙️", "MD": "⚙️", "MI": "⚙️", "DC": "⚡",
        }

        for fila in respuestas:
            icono_pos = iconos_pos.get(fila["posicion_actual"], "⚙️")
            icono_resp = ICONOS_ESTADO_RESPUESTA.get(fila["respuesta"], "⏳")
            grupos[icono_pos].append(f"{icono_resp} {fila['alias']}")

        nombres_grupo = {"🧤": "PORTEROS", "🛡️": "DEFENSAS", "⚙️": "MEDIOCAMPISTAS", "⚡": "DELANTEROS"}

        embed = discord.Embed(
            title=f"📋 Convocatoria — vs {partido['rival']}",
            description=f"{partido['fecha']} — {partido['hora']}",
            color=COLOR_CLUB
        )
        hay_datos = False
        for icono, nombres in grupos.items():
            if nombres:
                hay_datos = True
                embed.add_field(name=f"{icono} {nombres_grupo[icono]}", value="\n".join(nombres), inline=False)

        if not hay_datos:
            embed.description += "\n\nNadie respondió todavía."

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PartidosCog(bot))
          
