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

        embed = discord.Embed(title="⚙️ Configuración del servidor", color=discord.Color.blue())
        embed.add_field(name="Rol Staff", value=rol.mention if rol else "No configurado", inline=False)
        embed.set_footer(text="Usá r!config rol_staff @rol para configurarlo")
        await ctx.send(embed=embed)

    @config.command(name="rol_staff")
    @commands.has_permissions(administrator=True)
    async def rol_staff(self, ctx, rol: discord.Role):
        """Configura qué rol puede usar los comandos administrativos. Uso: r!config rol_staff @rol"""
        db.actualizar_config(ctx.guild.id, "staff_role_id", rol.id)
        await ctx.send(embed=embed_exito(f"Rol de staff configurado: {rol.mention}"))

    @config.error
    @rol_staff.error
    async def config_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=embed_error("Solo un administrador de Discord puede usar este comando."))
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send(embed=embed_error("No encontré ese rol. Mencionalo con @ o pasá su ID."))
        else:
            await ctx.send(embed=embed_error(f"Ocurrió un error: {error}"))


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
  
