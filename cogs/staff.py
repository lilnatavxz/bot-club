import discord
from discord.ext import commands
from database import db
from utils.permissions import solo_staff
from utils.embeds import embed_error, embed_exito
from utils.logs import registrar_log
from config.settings import ESTADOS_VALIDOS


class ConfirmarEliminar(discord.ui.View):
    def __init__(self, discord_id, alias):
        super().__init__(timeout=30)
        self.discord_id = discord_id
        self.alias = alias
        self.confirmado = None

    @discord.ui.button(label="Eliminar", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        db.eliminar_jugador(self.discord_id)
        await interaction.response.edit_message(
            embed=embed_exito(f"{self.alias} fue eliminado de la base de datos."), view=None
        )
        await registrar_log(interaction.client, interaction.guild, interaction.user, "Eliminó jugador", self.alias)
        self.confirmado = True
        self.stop()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(description="Operación cancelada.", color=discord.Color.greyple()), view=None
        )
        self.confirmado = False
        self.stop()


class SeleccionarCampo(discord.ui.Select):
    def __init__(self, discord_id):
        self.discord_id = discord_id
        opciones = [
            discord.SelectOption(label="Alias", value="alias"),
            discord.SelectOption(label="Posición principal", value="posicion_principal"),
            discord.SelectOption(label="Posiciones secundarias", value="posiciones_secundarias"),
            discord.SelectOption(label="Rango", value="rango"),
            discord.SelectOption(label="Estado", value="estado"),
            discord.SelectOption(label="Número", value="numero"),
        ]
        super().__init__(placeholder="Elegí qué querés modificar...", options=opciones)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✏️ Escribí el nuevo valor para **{self.values[0]}** en el chat (tenés 30 segundos):",
            ephemeral=True
        )

        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=30)
            valor_anterior = db.obtener_jugador(self.discord_id)[self.values[0]]
            db.actualizar_campo_jugador(self.discord_id, self.values[0], msg.content)
            await interaction.followup.send(embed=embed_exito(f"Campo **{self.values[0]}** actualizado."))
            jugador = db.obtener_jugador(self.discord_id)
            await registrar_log(
                interaction.client, interaction.guild, interaction.user,
                f"Modificó {self.values[0]}", jugador["alias"],
                f"{valor_anterior or '—'} → {msg.content}"
            )
        except TimeoutError:
            await interaction.followup.send(embed=embed_error("Se acabó el tiempo, no se hizo ningún cambio."))


class MenuEditar(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=60)
        self.add_item(SeleccionarCampo(discord_id))


class RegistroModal(discord.ui.Modal, title="Registrar jugador"):
    alias = discord.ui.TextInput(label="Alias", placeholder="Ej: Player01", max_length=32)
    posicion_principal = discord.ui.TextInput(label="Posición principal", placeholder="Ej: MC", max_length=10)
    posiciones_secundarias = discord.ui.TextInput(
        label="Posiciones secundarias (o 'ninguna')", placeholder="Ej: MCD, MCO",
        required=False, max_length=50
    )
    rango = discord.ui.TextInput(label="Rango", placeholder="Ej: Titular", required=False, max_length=30)

    def __init__(self, usuario: discord.Member):
        super().__init__()
        self.usuario = usuario

    async def on_submit(self, interaction: discord.Interaction):
        secundarias = self.posiciones_secundarias.value.strip()
        if secundarias.lower() in ("", "ninguna"):
            secundarias = ""

        db.registrar_jugador(
            self.usuario.id, interaction.guild.id, str(self.usuario),
            self.alias.value, self.posicion_principal.value,
            secundarias, self.rango.value or "Sin rango"
        )

        embed = discord.Embed(title="✅ Jugador registrado", color=discord.Color.green())
        embed.add_field(name="Discord", value=self.usuario.mention, inline=True)
        embed.add_field(name="Alias", value=self.alias.value, inline=True)
        embed.add_field(name="Posición principal", value=self.posicion_principal.value, inline=True)
        await interaction.response.send_message(embed=embed)
        await registrar_log(interaction.client, interaction.guild, interaction.user, "Registró jugador", self.alias.value)


class AbrirFormularioRegistro(discord.ui.View):
    def __init__(self, usuario: discord.Member, autor_id: int):
        super().__init__(timeout=180)
        self.usuario = usuario
        self.autor_id = autor_id

    @discord.ui.button(label="📝 Completar formulario de registro", style=discord.ButtonStyle.primary)
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message(
                "❌ Solo quien ejecutó el comando puede completar este formulario.", ephemeral=True
            )
            return
        await interaction.response.send_modal(RegistroModal(self.usuario))


class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="registrar")
    @solo_staff()
    async def registrar(self, ctx, usuario: discord.Member):
        """Abre un formulario para registrar un nuevo jugador. Uso: r!registrar @usuario"""
        embed = discord.Embed(
            description=f"Tocá el botón para abrir el formulario y registrar a {usuario.mention}.",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed, view=AbrirFormularioRegistro(usuario, ctx.author.id))

    @commands.command(name="editar")
    @solo_staff()
    async def editar(self, ctx, usuario: discord.Member):
        """Edita los datos de un jugador mediante un menú. Uso: r!editar @usuario"""
        jugador = db.obtener_jugador(usuario.id)
        if not jugador:
            await ctx.send(embed=embed_error("Ese usuario no está registrado."))
            return

        await ctx.send(f"Editando a **{jugador['alias']}**:", view=MenuEditar(usuario.id))

    @commands.command(name="eliminar")
    @solo_staff()
    async def eliminar(self, ctx, usuario: discord.Member):
        """Elimina a un jugador de la base de datos, con confirmación. Uso: r!eliminar @usuario"""
        jugador = db.obtener_jugador(usuario.id)
        if not jugador:
            await ctx.send(embed=embed_error("Ese usuario no está registrado."))
            return

        embed = discord.Embed(
            description=f"¿Seguro que querés eliminar a **{jugador['alias']}**? Esta acción no se puede deshacer.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, view=ConfirmarEliminar(usuario.id, jugador["alias"]))

    @commands.command(name="rango")
    @solo_staff()
    async def rango(self, ctx, usuario: discord.Member, *, nuevo_rango: str):
        """Cambia el rango de un jugador. Uso: r!rango @usuario NuevoRango"""
        jugador = db.obtener_jugador(usuario.id)
        if not jugador:
            await ctx.send(embed=embed_error("Ese usuario no está registrado."))
            return
        rango_anterior = jugador["rango"]
        db.actualizar_campo_jugador(usuario.id, "rango", nuevo_rango)
        await ctx.send(embed=embed_exito(f"Rango de {jugador['alias']} actualizado a **{nuevo_rango}**."))
        await registrar_log(
            self.bot, ctx.guild, ctx.author, "Cambió rango", jugador["alias"],
            f"{rango_anterior} → {nuevo_rango}"
        )

    @commands.command(name="estado")
    @solo_staff()
    async def estado(self, ctx, usuario: discord.Member, nuevo_estado: str):
        """Cambia el estado de un jugador (Activo/Inactivo/Ausente). Uso: r!estado @usuario Activo"""
        nuevo_estado = nuevo_estado.capitalize()
        if nuevo_estado not in ESTADOS_VALIDOS:
            await ctx.send(embed=embed_error(f"Estado inválido. Usá uno de: {', '.join(ESTADOS_VALIDOS)}"))
            return

        jugador = db.obtener_jugador(usuario.id)
        if not jugador:
            await ctx.send(embed=embed_error("Ese usuario no está registrado."))
            return

        estado_anterior = jugador["estado"]
        db.actualizar_campo_jugador(usuario.id, "estado", nuevo_estado)
        await ctx.send(embed=embed_exito(f"Estado de {jugador['alias']} actualizado a **{nuevo_estado}**."))
        await registrar_log(
            self.bot, ctx.guild, ctx.author, "Cambió estado", jugador["alias"],
            f"{estado_anterior} → {nuevo_estado}"
        )


async def setup(bot):
    await bot.add_cog(StaffCog(bot))
