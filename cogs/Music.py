import discord
from discord.ext import commands
from pathlib import Path
import yt_dlp
import random
import asyncio
import json

json_dir = Path(__file__).resolve().parents[1] / "json"

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open(json_dir / "Setting.json", "r", encoding="utf8") as jfile:
            self.Setting = json.load(jfile)

        self.play_list = []  # 播放列表
        self.current_track = None  # 目前正在播放的歌曲
        self.volume = float(self.Setting["volume"])  # 預設音量 (1.0 = 100%)
        self.ydl_opts = {
            'outtmpl': './tmp/%(title)s.%(ext)s',
            'format': 'bestaudio/best',
            'merge_output_format': 'mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    def play_next(self, vc):
        if self.play_list:
            next_file = self.play_list.pop(0)
            self.current_track = next_file
            source = discord.FFmpegPCMAudio(str(next_file))
            # 使用 PCMVolumeTransformer 以便後續調整音量
            transformer = discord.PCMVolumeTransformer(source, volume=self.volume)
            def after_playing(error):
                try:
                    if next_file.exists():
                        next_file.unlink()  # 刪除tmp資料夾中的檔案
                except Exception as e:
                    print(f"檔案刪除失敗: {e}")
                self.current_track = None
                self.bot.loop.call_soon_threadsafe(self.play_next, vc)
            vc.play(transformer, after=after_playing)
        else:
            self.current_track = None
            # 播放列表結束
            pass

    def get_music_names(ctx: discord.AutocompleteContext):
            query = ctx.value
            if not query or query.strip() == "":
                return []
            if query.startswith("http://") or query.startswith("https://"):
                return []

            search_query = f"ytsearch10:{query}"
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'extract_flat': True,
                'default_search': 'ytsearch'
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(search_query, download=False)
                    entries = info.get('entries', [])
                    titles = [entry.get("title") for entry in entries if entry.get("title")]
                    return [
                        discord.OptionChoice(name=title, value=title)
                        for title in titles
                    ]
                except Exception as e:
                    print(f"搜尋錯誤: {e}")
                    return []

    music = discord.SlashCommandGroup("music", "music command group")

    @music.command(
        description="播放音樂",
    )
    @discord.option(
        "search", 
        type=discord.SlashCommandOptionType.string, 
        description="name or url",
        autocomplete=get_music_names
    )
    async def play(self, ctx, search: str):
        # 檢查使用者是否在語音頻道
        if ctx.author.voice is None:
            await ctx.respond("你必須先加入一個語音頻道！")
            return

        channel = ctx.author.voice.channel
        await ctx.defer()

        Path('./tmp').mkdir(parents=True, exist_ok=True)

        # 若非連結則加上 ytsearch: 前置
        if not (search.startswith("http://") or search.startswith("https://")):
            search = "ytsearch:" + search

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
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

        await ctx.respond(f"已加入歌曲 {file_path.stem} 到播放列表！")

    @music.command(
        description="調整播放音量 (0-150%)"
    )
    @discord.option(
        "volume",
        type=discord.SlashCommandOptionType.integer,
        description="音量百分比",
    )
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！")
            return
        if volume < 0 or volume > 150:
            await ctx.respond("請輸入 0 到 150 之間的音量百分比！")
            return
        # 更新全局預設音量
        self.volume = volume / 100.0
        # 若目前正在播放的話，則即時更新音量
        if ctx.voice_client.source and isinstance(ctx.voice_client.source, discord.PCMVolumeTransformer):
            ctx.voice_client.source.volume = self.volume
        await ctx.respond(f"已將音量調整為 {volume}%！")

    @music.command(
        description="顯示播放清單",
    )
    async def queue(self, ctx):
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

    @music.command(
        description="暫停音樂",
    )
    async def pause(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！")
            return
        vc = ctx.voice_client
        if vc.is_playing():
            vc.pause()
            await ctx.respond("音樂已暫停！")
        else:
            await ctx.respond("目前沒有正在播放的音樂！")

    @music.command(
        description="恢復播放音樂",
    )
    async def resume(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！")
            return
        vc = ctx.voice_client
        if vc.is_paused():
            vc.resume()
            await ctx.respond("音樂已恢復播放！")
        else:
            await ctx.respond("目前音樂沒有暫停！")

    @music.command(
        description="停止播放音樂",
    )
    async def stop(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！")
            return
        self.play_list.clear()
        vc = ctx.voice_client
        vc.stop()
        await vc.disconnect()
        
        tmp_path = Path('./tmp')
        if tmp_path.exists():
            for file in tmp_path.iterdir():
                if file.is_file():
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"刪除檔案 {file} 失敗: {e}")
        await ctx.respond("音樂已停止！")
    
    @music.command(
        description="跳過目前播放的音樂",
    )
    async def skip(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！")
            return
        vc = ctx.voice_client
        vc.stop()
        await ctx.respond("已跳過目前播放的音樂！")

    @music.command(
        description="移除指定的歌曲",
    )
    @discord.option(
        "index", 
        type=discord.SlashCommandOptionType.integer, 
        description="歌曲編號"
    )
    async def remove(self, ctx, index: int):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！")
            return
        if index < 1 or index > len(self.play_list):
            await ctx.respond("歌曲編號不正確！")
            return
        removed_file = self.play_list.pop(index-1)

        if removed_file.exists():
            try:
                removed_file.unlink()
            except Exception as e:
                print(f"無法刪除 {removed_file.name}: {e}")
        await ctx.respond(f"已移除 {removed_file.name}！")

    @music.command(
        description="隨機播放",
    )
    async def random(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！")
            return
        random.shuffle(self.play_list)
        await ctx.respond("已隨機播放！")

    @music.command(
        description="播放指定的歌曲",
    )
    @discord.option(
        "index", 
        type=discord.SlashCommandOptionType.integer, 
        description="歌曲編號"
    )
    async def play_index(self, ctx, index: int):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！")
            return
        if index < 1 or index > len(self.play_list):
            await ctx.respond("歌曲編號不正確！")
            return
        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()
            # 等待播放狀態完全停止
            while vc.is_playing():
                await asyncio.sleep(0.1)
        self.play_list.insert(0, self.play_list.pop(index-1))
        self.play_next(vc)
        await ctx.respond(f"已播放 {self.current_track.name}！")

def setup(bot):
    bot.add_cog(Music(bot))