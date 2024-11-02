import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


class Owner(commands.Cog, name="owner"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(name="sync", description="Đồng bộ hoá slash commands.")
    @app_commands.describe(scope="Scope khi đồng bộ. Có thể là `global` hoặc `guild`")
    @commands.is_owner()
    async def sync(self, context: Context, scope: str) -> None:

        if scope == "global":
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands đã được đồng bộ hoá trên global.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.copy_global_to(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands đã được đồng bộ hoá ở guild này.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="Scope phải là `global` hoặc `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @commands.command(name="unsync", description="Huỷ đồng bộ hoá slash commands.")
    @app_commands.describe(
        scope="Scope khi huỷ đồng bộ. Có thể là `global` hoặc `guild`"
    )
    @commands.is_owner()
    async def unsync(self, context: Context, scope: str) -> None:

        if scope == "global":
            context.bot.tree.clear_commands(guild=None)
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands đã được huỷ đồng bộ trên global.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.clear_commands(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands đã được huỷ đồng bộ ở guild này.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="Scope phải là `global` hoặc `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @commands.hybrid_command(name="load", description="Tải lên một cog mới.")
    @app_commands.describe(cog="Tên của cog cần tải lên.")
    @commands.is_owner()
    async def load(self, context: Context, cog: str) -> None:
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Không thể tải `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Tải thành công `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(name="reload", description="Reload một cog.")
    @app_commands.describe(cog="Tên của cog cần reload.")
    @commands.is_owner()
    async def reload(self, context: Context, cog: str) -> None:

        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Không thể reload `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Reload thành công `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(name="say", description="Bot sẽ nói những gì bạn muốn.")
    @app_commands.describe(message="Thông điệp mà bạn muốn bot nói.")
    @commands.is_owner()
    async def say(self, context: Context, *, message: str) -> None:
        await context.send(message)

    @commands.hybrid_command(name="embed", description="Bot sẽ nói những gì bạn muốn, nhưng ở trong một embed.")
    @app_commands.describe(message="Thông điệp mà bạn muốn bot nói.")
    @commands.is_owner()
    async def embed(self, context: Context, *, message: str) -> None:
        embed = discord.Embed(description=message, color=0xBEBEFE)
        await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Owner(bot))
