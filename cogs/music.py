import random, asyncio, discord, json

from ast import alias
from discord.ext import commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
from cache.cache import RedisCache


class Music(commands.Cog,name="Music"):
    
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
            title = self.ytdl.extract_info(item, download = False)['title']
            return {'source':item,'title':title}
        search = VideosSearch(item,limit=1)
        return {'source':search.result()['result'][0]['link'],'title':search.result()['result'][0]['title']}
    
    async def play_next(self):
        if len(self.songQueue)>0:
            self.isPlaying = True
            m_url = self.songQueue[0][0]['source']
            
            self.songQueue.pop(0)
            
            #====================REDIS====================
            cache = RedisCache()
            if cache.get_song_url(m_url):
                song = cache.get_song_url(m_url)
                self.voiceChannel.play(discord.FFmpegPCMAudio(song,executable="ffmpeg",**self.FFMPEG_OPTIONS),after = lambda e: asyncio.run_coroutine_threadsafe(self.play_next(),self.bot.loop))
                return
            #============================================
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None,lambda: self.ytdl.extract_info(m_url, download = False)) #create new thread to get new song, non blocking main thread, only get infor
            song = data['url'] 
                
            cache.set_song_url(m_url,song)
                
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
                    await ctx.send('Lỗi kết nối đến voice channel')
                    return
            else:
                await self.voiceChannel.move_to(self.songQueue[0][1])
                
            self.songQueue.pop(0)
            #====================REDIS====================
            cache = RedisCache()
            if cache.get_song_url(m_url):
                song = cache.get_song_url(m_url)
                self.voiceChannel.play(discord.FFmpegPCMAudio(song, executable="ffmpeg", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
                return
            #============================================
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(m_url, download = False))

            # with open('output.json','w',encoding="utf-8") as file:
            #     json.dump(data, file, indent=4, ensure_ascii=False)
                
            song = data['url']
            cache.set_song_url(data['webpage_url'],song)
            self.voiceChannel.play(discord.FFmpegPCMAudio(song, executable= "ffmpeg", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
        else:
            self.isPlaying = False
    
    
    @commands.command(name="play",aliases=['p','playing'],description="Nhập tên một bài hát hoặc url youtube của nó")
    async def play(self,ctx,*args):
        query = " ".join(args)
        try:
            voiceChannel = ctx.author.voice.channel
        except:
            await ctx.send('Bạn phải ở trong voice channel để sử dụng lệnh này')
            return
        if self.isPaused:
            self.voiceChannel.resume()
        else:
            song = self.search(query)
            if type(song)==type(True):
                await ctx.send("Lỗi kết nối, vui lòng thử lại sau")
            else:
                if self.isPlaying == True:
                    await ctx.send(f"**#{len(self.songQueue)+2} -'{song['title']}'** đã được thêm vào danh sách phát")
                else:
                    await ctx.send(f"**'{song['title']}'** đã được thêm vào danh sách phát")   

                self.songQueue.append([song,voiceChannel])

                if self.isPlaying==False:
                    await self.play_music(ctx)
        
    @commands.command(name="pause",description="Tạm dừng")
    async def pause(self,ctx,*args):
        if self.isPlaying:
            self.voiceChannel.pause()
            self.isPaused = True
            self.isPlaying = False
            await ctx.send('Đã tạm dừng')
        elif self.isPaused:
            self.isPaused = False
            self.isPlaying = True
            self.voiceChannel.resume()
            await ctx.send('Đang phát')
    @commands.command(name="resume",description="Tiếp tục")
    async def resume(self,ctx,*args):
        if self.isPaused:
            self.isPaused = False
            self.isPlaying = True
            self.voiceChannel.resume()
            await ctx.send('Đang phát')
    @commands.command(name="skip", aliases=["s"], description="Bỏ qua bài hát hiện tại")
    async def skip(self,ctx):
        if self.isPlaying:
            self.voiceChannel.stop()
            await self.play_next()
            await ctx.send('Bài hát đã được bỏ qua')
        else:
            await ctx.send('Không có bài hát nào đang phát')
    @commands.command(name="queue",aliases=['q'],description="Hiển thị danh sách phát")
    async def queue(self,ctx):
        if len(self.songQueue)==0:
            await ctx.send('Không có bài hát nào trong danh sách phát')
        else:
            embed = discord.Embed(title="Danh sách phát",description="",color=discord.Color.green())
            i = 1
            for song in self.songQueue:
                embed.description += f"**{i} - {song[0]['title']}**\n"
                i+=1
            await ctx.send(embed=embed)
        print(self.songQueue)
    @commands.command(name="leave",aliases=['disconnect','dc'],description="Rời khỏi voice channel")
    async def leave(self,ctx):
        if self.voiceChannel != None:
            await self.voiceChannel.disconnect()
            self.voiceChannel = None
            self.songQueue = []
            self.isPlaying = False
            self.isPaused = False
            await ctx.send('Đã ngắt kết nối đến voice channel')
        else:
            await ctx.send('Bot không ở trong voice channel')
    @commands.command(name="clear_queue",description="Làm mới danh sách phát")
    async def clear(self,ctx):
        self.songQueue = []
        await ctx.send('Queue cleared')
    @commands.command(name="remove",description="Xóa bài hát khỏi danh sách phát")
    async def remove(self,ctx,*args):
        if len(args)==0:
            await ctx.send('Vui lòng nhập index của bài hát cần xóa')
        else:
            try:
                index = int(args[0])
                if index>0 and index<=len(self.songQueue):
                    song = self.songQueue[index-1][0]['title']
                    self.songQueue.pop(index-1)
                    await ctx.send(f"**'{song}'** đã được xóa khỏi danh sách phát")
                else:
                    await ctx.send('')
            except:
                await ctx.send('Bạn phải nhập một số  hợp lệ')
    @commands.command(name="shuffle",description="Xáo trộn danh sách phát")
    async def shuffle(self,ctx):
        if len(self.songQueue)>0:
            random.shuffle(self.songQueue)
            await ctx.send('Danh sách phát đã được xáo trộn')
            await self.queue(ctx)
        else:
            await ctx.send('Không có bài hát nào trong danh sách phát')
            
async def setup(bot) -> None:
    await bot.add_cog(Music(bot))