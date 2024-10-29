import random, asyncio, discord, json

from ast import alias
from discord.ext import commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
from cache.cache import RedisCache


class MusicPlayer:
    def __init__(self,bot,guild):
        self.bot = bot
        self.guild = guild
        self.voiceChannel = None
        self.songQueue = []
        self.isPlaying = False
        self.isPaused = False
        self.YDL_OPTIONS = {'format':'bestaudio','noplaylist':'True'}
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -filter:a "volume=1.5"'
        }
        
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)
        self.cache = RedisCache()
        
    def search_song(self,item):
        if item.startswith('https://'):
            title = self.ytdl.extract_info(item, download = False)['title']
            return {'source':item,'title':title}
        search = VideosSearch(item,limit=1)
        return {'source':search.result()['result'][0]['link'],'title':search.result()['result'][0]['title']}
    
    async def play_next(self):
        if len(self.songQueue)>0:
            self.isPlaying = True
            title = self.songQueue[0][0]['title']
            url = self.songQueue[0][0]['source']
            self.songQueue.pop(0)
            #check if song is in cache
            if cache_song:= self.cache.get_song_url(url):
                song = cache_song
                self.voiceChannel.play(discord.FFmpegPCMAudio(song,executable="ffmpeg",**self.FFMPEG_OPTIONS),after = lambda e: asyncio.run_coroutine_threadsafe(self.play_next(),self.bot.loop))
                return
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None,lambda: self.ytdl.extract_info(url, download = False))
            #cache it
            self.cache.set_song_url(url,data['url'])
            
            self.voiceChannel.play(discord.FFmpegPCMAudio(data['url'],executable="ffmpeg",**self.FFMPEG_OPTIONS),after = lambda e: asyncio.run_coroutine_threadsafe(self.play_next(),self.bot.loop))
            
        else:
            self.isPlaying = False
    async def play_song(self,ctx,song):
        self.songQueue.append([song,ctx.author.voice.channel])
        if not self.isPlaying:
            await self.play_next()
    async def connect_to_voice_channel(self,ctx):
        try:
            if ctx.voice_client is not None and ctx.voice_client.is_connected():
                if ctx.voice_client.channel!=ctx.author.voice.channel:
                    await ctx.voice_client.move_to(ctx.author.voice.channel)
                return
            self.voiceChannel = await ctx.author.voice.channel.connect()
        except:
            await ctx.send("Bạn phải ở trong voice channel để sử dụng lệnh này")
    def get_song_queue(self):
        return self.songQueue
    def set_song_queue(self,queue):
        self.songQueue = queue