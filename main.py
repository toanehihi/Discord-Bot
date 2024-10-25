import discord
from discord.ext import commands
import os, asyncio
from dotenv import load_dotenv
from Cogs.music import Music
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states= True


bot = commands.Bot(command_prefix='!',intents=intents)

@bot.event
async def on_ready():
    print('Bot is ready')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')
    
    
    
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="chung")
    if channel:
        await channel.send(f'Welcome {member.mention} to the server!')
    else:
        print('Channel not found')  

async def main():
    async with bot:
        load_dotenv()
        await bot.add_cog(Music(bot))
        await bot.start(os.getenv('DISCORD_API_TOKEN'))


asyncio.run(main())