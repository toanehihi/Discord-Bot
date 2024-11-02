import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="kick", description="Kick user chỉ định khỏi server.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(
        user="User bị kick.",
        reason="Lý do kick.",
    )
    async def kick(
        self, context: Context, user: discord.User, *, reason: str = "Không xác định"
    ) -> None:
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        if member.guild_permissions.administrator:
            embed = discord.Embed(
                description="User có quyền admin.", color=0xE02B2B
            )
            await context.send(embed=embed)
        else:
            try:
                embed = discord.Embed(
                    description=f"**{member}** đã bị kick bởi **{context.author}**!",
                    color=0xBEBEFE,
                )
                embed.add_field(name="Lý do:", value=reason)
                await context.send(embed=embed)
                try:
                    await member.send(
                        f"Bạn bị kick bởi **{context.author}** từ server **{
                            context.guild.name}**!\nReason: {reason}"
                    )
                except:
                    # Couldn't send a message for the user
                    pass
                await member.kick(reason=reason)
            except:
                embed = discord.Embed(
                    description="Có lỗi xảy ra khi kick. Đảm bảo bạn có quyền kick user khỏi server.",
                    color=0xE02B2B,
                )
                await context.send(embed=embed)

    @commands.hybrid_command(name="nick", description="Thay đổi nickname của một user trong server.")
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.describe(
        user="User được đổi nickname.",
        nickname="Nickname mới cho user.",
    )
    async def nick(
        self, context: Context, user: discord.User, *, nickname: str = None
    ) -> None:
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        try:
            await member.edit(nick=nickname)
            embed = discord.Embed(
                description=f"**{member}'s** có nickname mới là **{nickname}**!",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
        except:
            embed = discord.Embed(
                description="Có lỗi xảy ra khi đổi nickname. Đảm bảo rằng bạn có quyền đổi nickname người khác.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(name="ban", description="Cấm một user khỏi server.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user="User bị ban.",
        reason="Lý do ban.",
    )
    async def ban(
        self, context: Context, user: discord.User, *, reason: str = "Không xác định"
    ) -> None:
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(user.id)
        try:
            if member.guild_permissions.administrator:
                embed = discord.Embed(
                    description="User có quyền chặn.", color=0xE02B2B
                )
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    description=f"**{member}** đã bị chặn khỏi server bởi **{context.author}**!",
                    color=0xBEBEFE,
                )
                embed.add_field(name="Lý do:", value=reason)
                await context.send(embed=embed)
                try:
                    await member.send(
                        f"Bạn đã bị chặn bởi **{context.author}** từ server **{
                            context.guild.name}**!\nReason: {reason}"
                    )
                except:
                    # Couldn't send a message in the private messages of the user
                    pass
                await member.ban(reason=reason)
        except:
            embed = discord.Embed(
                title="Error!",
                description="Có lỗi xảy ra khi chặn user. Đảm bảo bạn có quyền chặn user khỏi server.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="clear",
        description="Xoá một số lượng tin nhắn.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="Số lượng tin nhắn sẽ xoá.")
    async def clear(self, context: Context, amount: int) -> None:
        await context.send("Đang xoá tin nhắn...") 
        purged_messages = await context.channel.purge(limit=amount + 2)
        embed = discord.Embed(
            description=f"**{context.author}** đã xoá **{
                len(purged_messages)-1}** tin nhắn!",
            color=0xBEBEFE,
        )
        await context.channel.send(embed=embed)
        
    
async def setup(bot) -> None:
    await bot.add_cog(Moderation(bot))
