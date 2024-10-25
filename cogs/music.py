from ast import alias
import asyncio
import discord
from discord.ext import commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL

class Music(commands.Cog):

    #init service
    def __init__(self,bot):
        self.bot = bot
        self.isPlaying = False
        self.isPaused = False
        
        self.songQueue= []
        self.YDL_OPTIONS = {'format':'bestaudio','noplaylist':'True'}

        self.FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn -filter:a "volume=1.5"'
        }   
        
        self.voiceChannel = None
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)
    
    #research on youtube
    def search(self,item):
        if item.startswith('https://'):
            title = self.ytdl.extract_info(item,download=False)['title']
            return {'source':item,'title':title}
        search = VideosSearch(item,limit=1)
        return {'source':search.result()['result'][0]['link'],'title':search.result()['result'][0]['title']}
    
    async def play_next(self):
        if len(self.songQueue)>0:
            self.isPlaying = True
            
            #get fist song in queue
            m_url = self.songQueue[0][0]['source']
            
            #remove it
            self.songQueue.pop(0)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None,lambda: self.ytdl.extract_info(m_url,download=False)) #create new thread to get new song, non blocking main thread, only get infor
            song = data['url'] #get url
            #pass in 1 callback to play next song
            self.voiceChannel.play(discord.FFmpegPCMAudio(song,executable="ffmpeg",**self.FFMPEG_OPTIONS),after = lambda e: asyncio.run_coroutine_threadsafe(self.play_next(),self.bot.loop))
        else:
            self.isPlaying = False
    #infinity loop check
    async def play_music(self,ctx):
        if len(self.songQueue)>0:
            self.isPlaying = True
            m_url = self.songQueue[0][0]['source']
            
            if self.voiceChannel==None or not self.voiceChannel.is_connected():
                self.voiceChannel = await self.songQueue[0][1].connect()
                
                if self.voiceChannel == None:
                    await ctx.send('Error connecting to voice channel')
                    return
            else:
                await self.voiceChannel.move_to(self.songQueue[0][1])
                
            self.songQueue.pop(0)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(m_url, download=False))
            song = data['url']
            print(song)
            self.voiceChannel.play(discord.FFmpegPCMAudio(song, executable= "ffmpeg", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
        else:
            self.isPlaying = False
    
    
    @commands.command(name="play",aliases=['p','playing'],help="Pick a song on Youtube to play")
    async def play(self,ctx,*args):
        query = " ".join(args)
        try:
            voiceChannel = ctx.author.voice.channel
            # if self.voiceChannel == None or not self.voiceChannel.is_connected():
            #     self.voiceChannel = await voiceChannel.connect()
            # if self.voiceChannel != voiceChannel:
            #     await self.voiceChannel.move_to(voiceChannel)
        except:
            await ctx.send('You are not in a voice channel, pls join one')
            return
        if self.isPaused:
            self.voiceChannel.resume()
        else:
            song = self.search(query)
            if type(song)==type(True):
                await ctx.send("Error, plz try again")
            else:
                if self.isPlaying == True:
                    await ctx.send(f"**#{len(self.songQueue)+2} -'{song['title']}'** added to the queue")
                else:
                    await ctx.send(f"**'{song['title']}'** added to the queue")   
                self.songQueue.append([song,voiceChannel])

                if self.isPlaying==False:
                    await self.play_music(ctx)
        
    @commands.command(name="pause",help="Pause the song")
    async def pause(self,ctx,*args):
        if self.isPlaying:
            self.voiceChannel.pause()
            self.isPaused = True
            self.isPlaying = False
            await ctx.send('Paused')
        elif self.isPaused:
            self.isPaused = False
            self.isPlaying = True
            self.voiceChannel.resume()
            await ctx.send('Resumed')
    @commands.command(name="resume",help="Resume the song")
    async def resume(self,ctx,*args):
        if self.isPaused:
            self.isPaused = False
            self.isPlaying = True
            self.voiceChannel.resume()
            await ctx.send('Resumed')
    @commands.command(name="skip", aliases=["s"], help="Skips the current song being played")
    async def skip(self,ctx):
        if self.isPlaying:
            self.voiceChannel.stop()
            await self.play_next()
            await ctx.send('Skipped')
        else:
            await ctx.send('No song is playing')
    @commands.command(name="queue",aliases=['q'],help="Shows the current queue")
    async def queue(self,ctx):
        if len(self.songQueue)==0:
            await ctx.send('No song in queue')
        else:
            embed = discord.Embed(title="Song Queue",description="",color=discord.Color.green())
            i = 1
            for song in self.songQueue:
                embed.description += f"**{i} - {song[0]['title']}**\n"
                i+=1
            await ctx.send(embed=embed)
    @commands.command(name="leave",aliases=['disconnect','dc'],help="Leave the voice channel")
    async def leave(self,ctx):
        if self.voiceChannel != None:
            await self.voiceChannel.disconnect()
            self.voiceChannel = None
            self.songQueue = []
            self.isPlaying = False
            self.isPaused = False
            await ctx.send('Disconnected')
        else:
            await ctx.send('Bot is not in a voice channel')
    @commands.command(name="clear",help="Clear the queue")
    async def clear(self,ctx):
        self.songQueue = []
        await ctx.send('Queue cleared')
    @commands.command(name="remove",help="Remove a song from the queue")
    async def remove(self,ctx,*args):
        if len(args)==0:
            await ctx.send('Plz provide the index of the song you want to remove')
        else:
            try:
                index = int(args[0])
                if index>0 and index<=len(self.songQueue):
                    song = self.songQueue[index-1][0]['title']
                    self.songQueue.pop(index-1)
                    await ctx.send(f"**'{song}'** removed from queue")
                else:
                    await ctx.send('Index out of range')
            except:
                await ctx.send('Invalid index')
    

