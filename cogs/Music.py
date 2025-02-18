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

        self.play_list = []
        self.current_track = None
        self.volume = float(self.Setting["Volume"])
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

    def play_next(self, vc):
        # 若還在播放中則延遲後再嘗試，避免重複播放
        if vc.is_playing():
            self.bot.loop.call_later(0.1, self.play_next, vc)
            return

        if self.play_list:
            next_file = self.play_list.pop(0)
            self.current_track = next_file
            source = discord.FFmpegPCMAudio(str(next_file))
            transformer = discord.PCMVolumeTransformer(source, volume=self.volume)

            def after_playing(error):
                try:
                    if next_file.exists():
                        next_file.unlink()  # 刪除 tmp 資料夾中的檔案
                except Exception as e:
                    print(f"檔案刪除失敗: {e}")
                self.current_track = None
                # 延遲一下再嘗試下一首
                self.bot.loop.call_later(0.5, self.play_next, vc)

            try:
                vc.play(transformer, after=after_playing)
            except discord.ClientException as e:
                print(f"播放錯誤: {e}")
                self.bot.loop.call_later(0.5, self.play_next, vc)
        else:
            self.current_track = None

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
            extracted = await asyncio.to_thread(ydl.extract_info, search, download=False)
            if 'entries' in extracted:
                # 處理歌單，先下載第一首並立即播放
                entries = extracted['entries']
                first_info = await asyncio.to_thread(
                    ydl.extract_info, entries[0]['webpage_url'], download=True
                )
                first_file = Path(ydl.prepare_filename(first_info)).with_suffix('.mp3')
                if not first_file.exists():
                    raise FileNotFoundError(f"No such file: {first_file}")
                self.play_list.append(first_file)

                # 取得語音連線
                vc = await self.ensure_voice_client(channel, ctx.voice_client)
                if not vc.is_playing():
                    self.play_next(vc)

                # 下載剩餘歌曲並加入播放列表
                for entry in entries[1:]:
                    song_info = await asyncio.to_thread(
                        ydl.extract_info, entry['webpage_url'], download=True
                    )
                    song_file = Path(ydl.prepare_filename(song_info)).with_suffix('.mp3')
                    if not song_file.exists():
                        raise FileNotFoundError(f"No such file: {song_file}")
                    self.play_list.append(song_file)
                playlist_info = f"{len(entries)} 首歌曲"
            else:
                # 非歌單情況
                info_downloaded = await asyncio.to_thread(ydl.extract_info, search, download=True)
                file_path = Path(ydl.prepare_filename(info_downloaded)).with_suffix('.mp3')
                if not file_path.exists():
                    raise FileNotFoundError(f"No such file: {file_path}")
                self.play_list.append(file_path)
                playlist_info = f"歌曲 {file_path.stem}"

        # 連線到使用者所在的語音頻道
        vc = await self.ensure_voice_client(channel, ctx.voice_client)

        # 若目前未播放任何音樂，即開始依序播放播放列表中的歌曲
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
        # 檢查使用者是否在語音頻道中
        if ctx.author.voice is None:
            await ctx.respond("你必須先加入一個語音頻道！")
            return
        channel = ctx.author.voice.channel

        # 使用 ensure_voice_client 方法建立或切換連線
        vc = await self.ensure_voice_client(channel, ctx.voice_client)
    
        if index < 1 or index > len(self.play_list):
            await ctx.respond("歌曲編號不正確！")
            return

        if vc.is_playing():
            vc.stop()
            # 等待播放狀態完全停止
            while vc.is_playing():
                await asyncio.sleep(0.1)
    
        # 將指定歌曲移至播放列表第一個位置
        self.play_list.insert(0, self.play_list.pop(index - 1))
        self.play_next(vc)
        await ctx.respond(f"已播放 {self.current_track.name}！")

def setup(bot):
    bot.add_cog(Music(bot))