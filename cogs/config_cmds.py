import discord
from discord.ext import commands
from database import db
from utils.embeds import embed_error, embed_exito


class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="config", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        conf = db.obtener_config(ctx.guild.id)
        rol = ctx.guild.get_role(conf["staff_role_id"]) if conf["staff_role_id"] else None
        c_registros = ctx.guild.get_channel(conf["canal_registros"]) if conf["canal_registros"] else None
        c_partidos = ctx.guild.get_channel(conf["canal_partidos"]) if conf["canal_partidos"] else None
        c_convocatorias = ctx.guild.get_channel(conf["canal_convocatorias"]) if conf["canal_convocatorias"] else None
        c_logs = ctx.guild.get_channel(conf["canal_logs"]) if conf["canal_logs"] else None

        embed = discord.Embed(title="⚙️ Configuración del servidor", color=discord.Color.blue())
        embed.add_field(name="Rol Staff", value=rol.mention if rol else "No configurado", inline=False)
        embed.add_field(name="Canal de registros", value=c_registros.mention if c_registros else "No configurado", inline=True)
        embed.add_field(name="Canal de partidos", value=c_partidos.mention if c_partidos else "No configurado", inline=True)
        embed.add_field(name="Canal de convocatorias", value=c_convocatorias.mention if c_convocatorias else "No configurado", inline=True)
        embed.add_field(name="Canal de logs", value=c_logs.mention if c_logs else "No configurado", inline=True)
        embed.add_field(name="Formación predeterminada", value=conf["formacion_predeterminada"] or "No configurada", inline=True)
        embed.add_field(name="Estado predeterminado", value=conf["estado_predeterminado"], inline=True)
        embed.set_footer(text="r!config <opción> <valor> — ej: r!config canal_logs #logs")
        await ctx.send(embed=embed)

    @config.command(name="rol_staff")
    @commands.has_permissions(administrator=True)
    async def rol_staff(self, ctx, rol: discord.Role):
        """Configura qué rol puede usar los comandos administrativos. Uso: r!config rol_staff @rol"""
        db.actualizar_config(ctx.guild.id, "staff_role_id", rol.id)
        await ctx.send(embed=embed_exito(f"Rol de staff configurado: {rol.mention}"))

    @config.command(name="canal_registros")
    @commands.has_permissions(administrator=True)
    async def canal_registros(self, ctx, canal: discord.TextChannel):
        """Configura el canal donde se anuncian los registros. Uso: r!config canal_registros #canal"""
        db.actualizar_config(ctx.guild.id, "canal_registros", canal.id)
        await ctx.send(embed=embed_exito(f"Canal de registros configurado: {canal.mention}"))

    @config.command(name="canal_partidos")
    @commands.has_permissions(administrator=True)
    async def canal_partidos(self, ctx, canal: discord.TextChannel):
        """Configura el canal donde se publican los partidos. Uso: r!config canal_partidos #canal"""
        db.actualizar_config(ctx.guild.id, "canal_partidos", canal.id)
        await ctx.send(embed=embed_exito(f"Canal de partidos configurado: {canal.mention}"))

    @config.command(name="canal_convocatorias")
    @commands.has_permissions(administrator=True)
    async def canal_convocatorias(self, ctx, canal: discord.TextChannel):
        """Configura el canal de convocatorias. Uso: r!config canal_convocatorias #canal"""
        db.actualizar_config(ctx.guild.id, "canal_convocatorias", canal.id)
        await ctx.send(embed=embed_exito(f"Canal de convocatorias configurado: {canal.mention}"))

    @config.command(name="canal_logs")
    @commands.has_permissions(administrator=True)
    async def canal_logs(self, ctx, canal: discord.TextChannel):
        """Configura el canal donde se registran las acciones de staff. Uso: r!config canal_logs #canal"""
        db.actualizar_config(ctx.guild.id, "canal_logs", canal.id)
        await ctx.send(embed=embed_exito(f"Canal de logs configurado: {canal.mention}"))

    @config.command(name="formacion")
    @commands.has_permissions(administrator=True)
    async def formacion_default(self, ctx, *, formacion: str):
        """Configura la formación predeterminada del club. Uso: r!config formacion 4-3-3"""
        db.actualizar_config(ctx.guild.id, "formacion_predeterminada", formacion)
        await ctx.send(embed=embed_exito(f"Formación predeterminada configurada: **{formacion}**"))

    @config.error
    @rol_staff.error
    @canal_registros.error
    @canal_partidos.error
    @canal_convocatorias.error
    @canal_logs.error
    @formacion_default.error
    async def config_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=embed_error("Solo un administrador de Discord puede usar este comando."))
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send(embed=embed_error("No encontré ese rol. Mencionalo con @ o pasá su ID."))
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send(embed=embed_error("No encontré ese canal. Mencionalo con # o pasá su ID."))
        else:
            await ctx.send(embed=embed_error(f"Ocurrió un error: {error}"))


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
