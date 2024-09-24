import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

intents.members = True


client = commands.Bot(command_prefix='!',intents=intents)

@client.event
async def on_ready():
    print('Bot is ready')

@client.command()
async def ping(ctx):
    await ctx.send('Pong!')
    
    
    
@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="chung")
    if channel:
        await channel.send(f'Welcome {member.mention} to the server!')
    else:
        print('Channel not found')  
    
    

load_dotenv()
client.run(os.getenv("DISCORD_API_TOKEN"))