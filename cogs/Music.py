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

        self.default_volume = float(self.Setting["Volume"])
        self.guild_data = {}  # guild_id -> {"play_list": [], "current_track": None, "volume": <float>}
        self.file_usage = {}  # 全域，用來記錄每首檔案的使用次數
        
        self.ydl_opts = {
            'outtmpl': './tmp/%(title)s.%(ext)s',
            'format': 'bestaudio/best',
            'merge_output_format': 'mp3',
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    def get_guild_data(self, guild: discord.Guild):
        if guild.id not in self.guild_data:
            self.guild_data[guild.id] = {
                "play_list": [],
                "current_track": None,
                "volume": self.default_volume
            }
        return self.guild_data[guild.id]

    def play_next(self, vc):
        data = self.get_guild_data(vc.guild)
        if vc.is_playing():
            self.bot.loop.call_later(0.1, self.play_next, vc)
            return

        if data["play_list"]:
            next_file = data["play_list"].pop(0)
            data["current_track"] = next_file
            source = discord.FFmpegPCMAudio(str(next_file))
            transformer = discord.PCMVolumeTransformer(source, volume=data["volume"])

            def after_playing(error):
                usage = self.file_usage.get(str(next_file), 0)
                if usage > 1:
                    self.file_usage[str(next_file)] = usage - 1
                else:
                    try:
                        if next_file.exists():
                            next_file.unlink()
                    except Exception as e:
                        print(f"檔案刪除失敗: {e}")
                    if str(next_file) in self.file_usage:
                        del self.file_usage[str(next_file)]
                data["current_track"] = None
                self.bot.loop.call_later(0.5, self.play_next, vc)
    
            try:
                vc.play(transformer, after=after_playing)
            except discord.ClientException as e:
                print(f"播放錯誤: {e}")
                self.bot.loop.call_later(0.5, self.play_next, vc)
        else:
            data["current_track"] = None

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
                
    async def ensure_voice_client(self, channel, voice_client):
        if voice_client is None:
            return await channel.connect()
        if voice_client.channel != channel:
            await voice_client.move_to(channel)
        if not voice_client.is_connected():
            return await channel.connect()
        return voice_client

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
        if ctx.author.voice is None:
            await ctx.respond("你必須先加入一個語音頻道！")
            return
        channel = ctx.author.voice.channel
        await ctx.defer()
        Path('./tmp').mkdir(parents=True, exist_ok=True)

        if not (search.startswith("http://") or search.startswith("https://")):
            search = "ytsearch:" + search

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            extracted = await asyncio.to_thread(ydl.extract_info, search, download=False)

            async def get_or_download(url):
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                file_path = Path(ydl.prepare_filename(info)).with_suffix('.mp3')
                if not file_path.exists():
                    info = await asyncio.to_thread(ydl.extract_info, url, download=True)
                    file_path = Path(ydl.prepare_filename(info)).with_suffix('.mp3')
                return file_path

            data = self.get_guild_data(ctx.guild)
            if 'entries' in extracted:
                entries = extracted['entries']
                if len(entries) == 1:
                    file_path = await get_or_download(entries[0]['webpage_url'])
                    data["play_list"].append(file_path)
                    self.file_usage[str(file_path)] = self.file_usage.get(str(file_path), 0) + 1
                    playlist_info = f"歌曲 {file_path.stem}"
                else:
                    first_file = await get_or_download(entries[0]['webpage_url'])
                    data["play_list"].append(first_file)
                    self.file_usage[str(first_file)] = self.file_usage.get(str(first_file), 0) + 1

                    vc = await self.ensure_voice_client(channel, ctx.voice_client)
                    if not vc.is_playing():
                        self.play_next(vc)

                    for entry in entries[1:]:
                        song_file = await get_or_download(entry['webpage_url'])
                        data["play_list"].append(song_file)
                        self.file_usage[str(song_file)] = self.file_usage.get(str(song_file), 0) + 1
                    playlist_info = f"{len(entries)} 首歌曲"
            else:
                file_path = await get_or_download(search)   
                data["play_list"].append(file_path)
                self.file_usage[str(file_path)] = self.file_usage.get(str(file_path), 0) + 1
                playlist_info = f"歌曲 {file_path.stem}"

        vc = await self.ensure_voice_client(channel, ctx.voice_client)
        if not vc.is_playing():
            self.play_next(vc)
        await ctx.respond(f"已加入 {playlist_info} 到播放列表！")

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
        data = self.get_guild_data(ctx.guild)
        data["volume"] = volume / 100.0
        if ctx.voice_client.source and isinstance(ctx.voice_client.source, discord.PCMVolumeTransformer):
            ctx.voice_client.source.volume = data["volume"]
        await ctx.respond(f"已將音量調整為 {volume}%！")

    @music.command(
        description="顯示播放清單",
    )
    async def queue(self, ctx):
        data = self.get_guild_data(ctx.guild)
        color = random.randint(0, 16777215)
        embed = discord.Embed(title="播放列表", color=color)
        if data["current_track"] is not None:
            embed.add_field(name="正在播放", value=data["current_track"].name, inline=False)
        if data["play_list"]:
            playlist_str = ""
            for i, file in enumerate(data["play_list"]):
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
        data = self.get_guild_data(ctx.guild)
        data["play_list"].clear()
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
        data = self.get_guild_data(ctx.guild)
        if index < 1 or index > len(data["play_list"]):
            await ctx.respond("歌曲編號不正確！")
            return
        removed_file = data["play_list"].pop(index-1)
        usage = self.file_usage.get(str(removed_file), 0)
        if usage > 1:
            self.file_usage[str(removed_file)] = usage - 1
        else:
            try:
                if removed_file.exists():
                    removed_file.unlink()
            except Exception as e:
                print(f"無法刪除 {removed_file.name}: {e}")
            if str(removed_file) in self.file_usage:
                del self.file_usage[str(removed_file)]
        await ctx.respond(f"已移除 {removed_file.name}！")

    @music.command(
        description="隨機播放",
    )
    async def random(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！")
            return
        data = self.get_guild_data(ctx.guild)
        random.shuffle(data["play_list"])
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
        if ctx.author.voice is None:
            await ctx.respond("你必須先加入一個語音頻道！")
            return
        channel = ctx.author.voice.channel
        data = self.get_guild_data(ctx.guild)
        vc = await self.ensure_voice_client(channel, ctx.voice_client)
    
        if index < 1 or index > len(data["play_list"]):
            await ctx.respond("歌曲編號不正確！")
            return

        if vc.is_playing():
            vc.stop()
            while vc.is_playing():
                await asyncio.sleep(0.1)
    
        data["play_list"].insert(0, data["play_list"].pop(index - 1))
        self.play_next(vc)
        await ctx.respond(f"已播放 {data['current_track'].name}！")

def setup(bot):
    bot.add_cog(Music(bot))