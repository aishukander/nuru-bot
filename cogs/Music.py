import discord
from discord.ext import commands
from pathlib import Path
import yt_dlp
import random

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.play_list = []  # 播放列表
        self.current_track = None  # 目前正在播放的歌曲

    def play_next(self, vc):
        if self.play_list:
            next_file = self.play_list.pop(0)
            self.current_track = next_file
            source = discord.FFmpegPCMAudio(str(next_file))
            def after_playing(error):
                try:
                    if next_file.exists():
                        next_file.unlink()  # 刪除tmp資料夾中的檔案
                except Exception as e:
                    print(f"檔案刪除失敗: {e}")
                self.current_track = None
                self.bot.loop.call_soon_threadsafe(self.play_next, vc)
            vc.play(source, after=after_playing)
        else:
            self.current_track = None
            # 播放列表結束
            pass

    music = discord.SlashCommandGroup("music", "music command group")

    @music.command(
        description="play music",
    )
    @discord.option(
        "search", 
        type=discord.SlashCommandOptionType.string, 
        description="name or url", 
    )
    async def play(self, ctx, search: str):
        # 檢查使用者是否在語音頻道
        if ctx.author.voice is None:
            await ctx.respond("你必須先加入一個語音頻道！")
            return

        channel = ctx.author.voice.channel
        await ctx.defer()

        ydl_opts = {
            'outtmpl': './tmp/%(title)s.%(ext)s',
            'format': 'bestaudio/best',
            'merge_output_format': 'mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        Path('./tmp').mkdir(parents=True, exist_ok=True)

        # 若非連結則加上 ytsearch: 前置
        if not (search.startswith("http://") or search.startswith("https://")):
            search = "ytsearch:" + search

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            original_file_path = Path(ydl.prepare_filename(info))
            file_path = original_file_path.with_suffix('.mp3')

        if not file_path.exists():
            raise FileNotFoundError(f"No such file: {file_path}")

        # 將下載完成的檔案加入播放列表
        self.play_list.append(file_path)

        # 連線到使用者所在的語音頻道
        if ctx.voice_client is None:
            vc = await channel.connect()
        else:
            vc = ctx.voice_client
            if vc.channel != channel:
                await vc.move_to(channel)
            # 檢查連線狀態，如已斷線則重新連線
            if not vc.is_connected():
                vc = await channel.connect()

        # 若目前未播放任何音樂，即開始依序播放列表中的歌曲
        if not vc.is_playing():
            self.play_next(vc)

        await ctx.respond(f"已加入歌曲 {file_path.name} 到播放列表！")

    @music.command(
        description="The playlist is displayed",
    )
    async def playlist(self, ctx):
        color = random.randint(0, 16777215)
        embed = discord.Embed(title="播放列表", color=color)
        if self.current_track is not None:
            embed.add_field(name="正在播放", value=self.current_track.name, inline=False)
        if self.play_list:
            playlist_str = ""
            for i, file in enumerate(self.play_list):
                playlist_str += f"{i+1}. {file.name}\n"
            embed.add_field(name="即將播放的歌曲", value=playlist_str, inline=False)
        if not embed.fields:
            embed.description = "播放列表是空的！"
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Music(bot))