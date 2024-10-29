import random, asyncio, discord, json

from ast import alias
from discord.ext import commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
from cache.cache import RedisCache
from util.util_music import MusicPlayer
#setup cog
async def setup(bot) -> None:
    await bot.add_cog(Music(bot))

class Music(commands.Cog,name="Music"):
    
    #init service
    def __init__(self,bot):
        self.bot = bot
        self.musicPlayers = {}
        
    def get_music_player(self,ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.musicPlayers:
            self.musicPlayers[guild_id] = MusicPlayer(self.bot,ctx.guild)
        return self.musicPlayers[guild_id]
    @commands.command(name="play", description="Phát nhạc từ YouTube")
    async def play(self, ctx, *args):
        if ctx.author.voice is None:
            await ctx.send("Bạn phải vào voice channel trước")
            return
        query = " ".join(args)
        player = self.get_music_player(ctx)
        await player.connect_to_voice_channel(ctx)
        song = player.search_song(query)
        await player.play_song(ctx,song)
        await ctx.send(f"**#{len(player.get_song_queue())+1} -'{song['title']}'** đã được thêm vào danh sách phát")
    
    @commands.command(name="skip", description="Bỏ qua bài hát hiện tại")
    async def skip(self, ctx):
        player = self.get_music_player(ctx)
        if player.voiceChannel:
            player.voiceChannel.stop()
            await player.play_next()
            await ctx.send("Bài hát đã được bỏ qua")
        else:
            await ctx.send("Bot chưa phát bài hát nào")
    @commands.command(name="pause", description="Tạm dừng bài hát")
    async def pause(self, ctx):
        player = self.get_music_player(ctx)
        if player.voiceChannel:
            if player.voiceChannel.is_playing():
                player.voiceChannel.pause()
                await ctx.send("Bài hát đã được tạm dừng")
            else:
                await ctx.send("Bot chưa phát bài hát nào")
        else:
            await ctx.send("Bot chưa vào voice channel nào")
    @commands.command(name="resume", description="Tiếp tục phát bài hát")
    async def resume(self, ctx):
        player = self.get_music_player(ctx)
        if player.voiceChannel:
            if player.voiceChannel.is_paused():
                player.voiceChannel.resume()
                await ctx.send("Bài hát đã được tiếp tục")
            else:
                await ctx.send("Bot chưa phát bài hát nào")
        else:
            await ctx.send("Bot chưa vào voice channel nào")
    @commands.command(name="leave", description="Rời khỏi voice channel")
    async def leave(self,ctx):
        player = self.get_music_player(ctx)
        if player.voiceChannel:
            await player.voiceChannel.disconnect()
            player.voiceChannel = None
            await ctx.send("Bot đã rời khỏi voice channel")
        else:
            await ctx.send("Bot chưa vào voice channel nào")
    @commands.command(name="queue", description="Hiển thị danh sách phát")
    async def queue(self,ctx):
        player = self.get_music_player(ctx)
        if len(player.songQueue)>0:
            embed = discord.Embed(title="Danh sách phát",color=discord.Color.green())
            for i,song in enumerate(player.songQueue):
                embed.add_field(name=f"#{i+1}",value=song[0]['title'],inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Danh sách phát trống")
    @commands.command(name="shuffle", description="Xáo trộn danh sách phát")
    async def shuffle(self,ctx):
        player = self.get_music_player(ctx)
        songQueue = player.get_song_queue()
        if len(songQueue)>0:
            random.shuffle(songQueue)
            player.set_song_queue(songQueue)
            await ctx.send("Danh sách phát đã được xáo trộn")
        else:
            await ctx.send("Danh sách phát trống")
    @commands.command(name="clear_queue", description="Xóa danh sách phát")
    async def clear_queue(self,ctx):
        player = self.get_music_player(ctx)
        player.set_song_queue([])
        await ctx.send("Danh sách phát đã được xóa")
        
