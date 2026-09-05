import discord
from discord.ext import commands
from utils.embeds import embed_error, embed_exito
from utils.permissions import es_encargado

ESTRUCTURA = {
    "🏆 Primer Equipo": {
        "rol": "Primer Equipo",
        "canales": ["general", "anuncios", "partidos"],
    },
    "🌱 Cantera": {
        "rol": "Cantera",
        "canales": ["general", "anuncios", "entrenamientos"],
    },
    "🔍 Visorías": {
        "rol": "Visorías",
        "canales": ["general", "pruebas"],
    },
}

SECCIONES_VALIDAS = {
    "primer_equipo": "Primer Equipo",
    "cantera": "Cantera",
    "visorias": "Visorías",
}


class SetupServidorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setup_estructura")
    @commands.has_permissions(administrator=True)
    async def setup_estructura(self, ctx):
        """Crea las categorías, roles y canales para Primer Equipo, Cantera y Visorías, con permisos separados."""
        guild = ctx.guild
        resumen = []

        # Rol Encargados: ve las 3 secciones y puede usar los comandos de gestión del bot
        rol_encargados = discord.utils.get(guild.roles, name="Encargados")
        if not rol_encargados:
            rol_encargados = await guild.create_role(
                name="Encargados", mentionable=True, color=discord.Color.gold()
            )

        for nombre_categoria, datos in ESTRUCTURA.items():
            rol_seccion = discord.utils.get(guild.roles, name=datos["rol"])
            if not rol_seccion:
                rol_seccion = await guild.create_role(name=datos["rol"], mentionable=True)

            # Nadie ve la categoría salvo su rol de sección y Encargados
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                rol_seccion: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                rol_encargados: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }

            categoria = discord.utils.get(guild.categories, name=nombre_categoria)
            if not categoria:
                categoria = await guild.create_category(nombre_categoria, overwrites=overwrites)
            else:
                await categoria.edit(overwrites=overwrites)

            for nombre_canal in datos["canales"]:
                existe = discord.utils.get(categoria.channels, name=nombre_canal)
                if not existe:
                    await guild.create_text_channel(nombre_canal, category=categoria)

            resumen.append(
                f"**{nombre_categoria}**\n"
                f"Rol: {rol_seccion.mention}\n"
                f"Canales: {', '.join(datos['canales'])}"
            )

        embed = discord.Embed(
            title="✅ Estructura del servidor creada",
            description="\n\n".join(resumen),
            color=discord.Color.green()
        )
        embed.add_field(
            name="👑 Rol Encargados",
            value=f"{rol_encargados.mention} — ve las 3 secciones y puede usar `r!partido crear`, "
                  f"`r!partido finalizar` y `r!asignar_seccion`",
            inline=False
        )
        embed.set_footer(text="Usá r!asignar_seccion @usuario <sección> para darle acceso a alguien")
        await ctx.send(embed=embed)

    @commands.command(name="asignar_seccion")
    async def asignar_seccion(self, ctx, usuario: discord.Member, seccion: str):
        """Le da a alguien el rol de una sección. Uso: r!asignar_seccion @usuario primer_equipo/cantera/visorias"""
        if not es_encargado(ctx.author):
            await ctx.send(embed=embed_error("No tienes permisos para utilizar este comando."))
            return

        seccion = seccion.lower()
        if seccion not in SECCIONES_VALIDAS:
            await ctx.send(embed=embed_error(
                f"Sección inválida. Usá una de: {', '.join(SECCIONES_VALIDAS.keys())}"
            ))
            return

        nombre_rol = SECCIONES_VALIDAS[seccion]
        rol = discord.utils.get(ctx.guild.roles, name=nombre_rol)
        if not rol:
            await ctx.send(embed=embed_error(
                f"No existe el rol \"{nombre_rol}\" todavía. Corré primero `r!setup_estructura`."
            ))
            return

        await usuario.add_roles(rol)
        await ctx.send(embed=embed_exito(f"{usuario.mention} ahora puede ver los canales de **{nombre_rol}**."))

    @setup_estructura.error
    async def setup_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=embed_error("Solo un administrador del servidor puede usar este comando."))
        elif isinstance(error, discord.Forbidden):
            await ctx.send(embed=embed_error(
                "No tengo permisos suficientes para crear roles/canales. "
                "Revisá que mi rol de bot esté arriba en la lista de roles del servidor."
            ))
        else:
            await ctx.send(embed=embed_error(f"Ocurrió un error: {error}"))

    @asignar_seccion.error
    async def asignar_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send(embed=embed_error("No encontré a ese usuario. Mencionalo con @."))
        else:
            await ctx.send(embed=embed_error(f"Ocurrió un error: {error}"))


async def setup(bot):
    await bot.add_cog(SetupServidorCog(bot))
      
