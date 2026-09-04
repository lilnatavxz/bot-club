import discord
from discord.ext import commands
from database import db
from utils.embeds import embed_error, embed_perfil
from config.settings import COLOR_CLUB

JUGADORES_POR_PAGINA = 8


class SeleccionarPosicion(discord.ui.Select):
    def __init__(self, discord_id, opciones_posiciones):
        self.discord_id = discord_id
        opciones = [discord.SelectOption(label=p, value=p) for p in opciones_posiciones]
        super().__init__(placeholder="Elegí tu posición actual...", options=opciones)

    async def callback(self, interaction: discord.Interaction):
        db.actualizar_campo_jugador(self.discord_id, "posicion_actual", self.values[0])
        await interaction.response.edit_message(
            content=f"✅ Tu posición actual ahora es **{self.values[0]}**.", view=None
        )


class MenuPosiciones(discord.ui.View):
    def __init__(self, discord_id, opciones_posiciones):
        super().__init__(timeout=60)
        self.add_item(SeleccionarPosicion(discord_id, opciones_posiciones))


class PerfilView(discord.ui.View):
    def __init__(self, jugador):
        super().__init__(timeout=60)
        self.jugador = jugador

    @discord.ui.button(label="Cambiar posición", style=discord.ButtonStyle.primary, emoji="🔄")
    async def cambiar_posicion(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.jugador["discord_id"]:
            await interaction.response.send_message("❌ Solo el dueño del perfil puede cambiar su posición.", ephemeral=True)
            return

        opciones = [self.jugador["posicion_principal"]]
        if self.jugador["posiciones_secundarias"]:
            opciones += [p.strip() for p in self.jugador["posiciones_secundarias"].split(",") if p.strip()]
        opciones = list(dict.fromkeys(opciones))  # sin duplicados

        await interaction.response.send_message(
            "Elegí tu nueva posición:", view=MenuPosiciones(self.jugador["discord_id"], opciones), ephemeral=True
        )


class ListaJugadoresView(discord.ui.View):
    def __init__(self, jugadores, guild_name):
        super().__init__(timeout=120)
        self.jugadores = jugadores
        self.guild_name = guild_name
        self.pagina = 0
        self.total_paginas = max(1, (len(jugadores) - 1) // JUGADORES_POR_PAGINA + 1)
        self._actualizar_botones()

    def _actualizar_botones(self):
        self.anterior.disabled = self.pagina == 0
        self.siguiente.disabled = self.pagina >= self.total_paginas - 1

    def construir_embed(self):
        inicio = self.pagina * JUGADORES_POR_PAGINA
        fin = inicio + JUGADORES_POR_PAGINA
        embed = discord.Embed(title=f"📋 Jugadores — {self.guild_name}", color=COLOR_CLUB)
        for j in self.jugadores[inicio:fin]:
            icono = {"Activo": "🟢", "Inactivo": "🔴", "Ausente": "🟡"}.get(j["estado"], "⚪")
            embed.add_field(
                name=f"{icono} {j['alias']}",
                value=f"Posición: {j['posicion_actual']}\nSecundarias: {j['posiciones_secundarias'] or '—'}",
                inline=True
            )
        embed.set_footer(text=f"Página {self.pagina + 1}/{self.total_paginas}")
        return embed

    @discord.ui.button(label="◀️ Anterior", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina -= 1
        self._actualizar_botones()
        await interaction.response.edit_message(embed=self.construir_embed(), view=self)

    @discord.ui.button(label="Siguiente ▶️", style=discord.ButtonStyle.secondary)
    async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina += 1
        self._actualizar_botones()
        await interaction.response.edit_message(embed=self.construir_embed(), view=self)


class JugadorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="yo")
    async def yo(self, ctx):
        """Muestra tu propio perfil de jugador."""
        jugador = db.obtener_jugador(ctx.author.id)
        if not jugador:
            await ctx.send(embed=embed_error("No estás registrado todavía. Pedile a un staff que use `r!registrar`."))
            return
        await ctx.send(embed=embed_perfil(jugador, es_propio=True), view=PerfilView(jugador))

    @commands.command(name="perfil")
    async def perfil(self, ctx, usuario: discord.Member):
        """Muestra el perfil público de otro jugador. Uso: r!perfil @usuario"""
        jugador = db.obtener_jugador(usuario.id)
        if not jugador:
            await ctx.send(embed=embed_error("Ese usuario no está registrado."))
            return
        await ctx.send(embed=embed_perfil(jugador))

    @commands.command(name="posiciones")
    async def posiciones(self, ctx):
        """Elegí cuál de tus posiciones vas a usar actualmente."""
        jugador = db.obtener_jugador(ctx.author.id)
        if not jugador:
            await ctx.send(embed=embed_error("No estás registrado todavía."))
            return

        opciones = [jugador["posicion_principal"]]
        if jugador["posiciones_secundarias"]:
            opciones += [p.strip() for p in jugador["posiciones_secundarias"].split(",") if p.strip()]
        opciones = list(dict.fromkeys(opciones))

        await ctx.send("Elegí la posición que vas a utilizar:", view=MenuPosiciones(ctx.author.id, opciones))

    @commands.command(name="jugadores")
    async def jugadores(self, ctx):
        """Muestra la lista de jugadores registrados, con paginación."""
        jugadores = db.obtener_jugadores(ctx.guild.id)
        if not jugadores:
            await ctx.send(embed=embed_error("Todavía no hay jugadores registrados."))
            return

        vista = ListaJugadoresView(jugadores, ctx.guild.name)
        await ctx.send(embed=vista.construir_embed(), view=vista)


async def setup(bot):
    await bot.add_cog(JugadorCog(bot))
      
