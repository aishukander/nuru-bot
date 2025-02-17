import discord
from discord.ext import commands
from pathlib import Path
import discord
import yt_dlp
import os

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        description="play music",
    )
    @discord.option(
        "url", 
        type=discord.SlashCommandOptionType.string, 
        description="url", 
    )
    async def play(self, ctx, url: str):
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

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # 利用 yt_dlp 自己產生經過 sanitize 的檔名，再轉換成 mp3 檔案名稱
            original_file_path = Path(ydl.prepare_filename(info))
            file_path = original_file_path.with_suffix('.mp3')

            if not file_path.exists():
                raise FileNotFoundError(f"No such file: {file_path}")

            await ctx.respond(file=discord.File(file_path))

def setup(bot):
    bot.add_cog(Music(bot))