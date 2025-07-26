import discord
from discord.ext import commands
from pathlib import Path
import yt_dlp
import random
import asyncio
import tomllib

toml_dir = Path(__file__).resolve().parents[1] / "toml"

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open(toml_dir / "Setting.toml", "rb") as tfile:
            self.Setting = tomllib.load(tfile)

        self.default_volume = float(self.Setting["Volume"])
        self.inactive_timeout = int(self.Setting["Inactive_Timeout"]) # 單位秒
        self.progress_bars = self.Setting["Progress_Bars"]
        self.bar_length = 20
        self.guild_data = {}  # guild_id -> {"play_list": [], "current_track": None, "volume": <float>, "inactive_task": None}
        self.file_usage = {}
        
        self.ydl_opts = {
            'outtmpl': './tmp/%(title)s.%(ext)s',
            'format': 'bestaudio[acodec=opus]/bestaudio/best',
            'format': 'bestaudio/best',
            'merge_output_format': 'opus',
            'quiet': True,
            'no_warnings': True,
            'audio_quality': 0,
            'concurrent_fragment_downloads': int(self.Setting["Music_Concurrent_Downloads"]),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '320',
            }],
            'ffmpeg_args': ['-af', 'loudnorm=I=-16:TP=-1.5:LRA=11'],
        }

    def get_guild_data(self, guild: discord.Guild):
        if guild.id not in self.guild_data:
            self.guild_data[guild.id] = {
                "play_list": [],
                "current_track": None,
                "volume": self.default_volume,
                "inactive_task": None
            }
        return self.guild_data[guild.id]

    async def check_inactivity(self, guild_id: int):
        await asyncio.sleep(self.inactive_timeout)
        data = self.guild_data.get(guild_id)
        if data and data["inactive_task"]:
            voice_client = self.bot.get_guild(guild_id).voice_client
            if voice_client and not voice_client.is_playing():
                await voice_client.disconnect()
                data["inactive_task"] = None

    def play_next(self, vc):
        server = self.get_guild_data(vc.guild)
        
        # 重設計時器
        if server["inactive_task"]:
            server["inactive_task"].cancel()
        server["inactive_task"] = asyncio.create_task(
            self.check_inactivity(vc.guild.id)
        )

        if vc.is_playing():
            self.bot.loop.call_later(0.1, self.play_next, vc)
            return

        if server["play_list"]:
            next_file = server["play_list"].pop(0)
            server["current_track"] = next_file
            source = discord.FFmpegPCMAudio(str(next_file))
            transformer = discord.PCMVolumeTransformer(source, volume=server["volume"])

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
                server["current_track"] = None
                self.bot.loop.call_later(0.5, self.play_next, vc)
    
            try:
                vc.play(transformer, after=after_playing)
            except discord.ClientException as e:
                print(f"播放錯誤: {e}")
                self.bot.loop.call_later(0.5, self.play_next, vc)
        else:
            server["current_track"] = None
            # 當播放列表為空時也要檢查是否需要離開
            if server["inactive_task"]:
                server["inactive_task"].cancel()
            server["inactive_task"] = asyncio.create_task(
                self.check_inactivity(vc.guild.id)
            )

    @staticmethod
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

    @music.command(description="播放音樂")
    @discord.option(
        "search", 
        type=discord.SlashCommandOptionType.string, 
        description="name or url",
        autocomplete=get_music_names
    )
    async def play(self, ctx, search: str):
        if ctx.author.voice is None:
            await ctx.respond("你必須先加入一個語音頻道！", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        await ctx.defer(ephemeral=True)
        Path('./tmp').mkdir(parents=True, exist_ok=True)

        if not (search.startswith("http://") or search.startswith("https://")):
            search = "ytsearch:" + search

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            extracted = await asyncio.to_thread(ydl.extract_info, search, download=False)

            async def get_or_download(url, progress_message, current, total):
                # 設置任務名稱
                current_task = asyncio.current_task()
                if current_task:
                    current_task.set_name(f'yt_dlp_download_{url}')

                # 計算完成的比例
                progress_ratio = (current - 1) / total
                # 計算已完成和未完成的區塊數
                filled_length = int(self.bar_length * progress_ratio)
                remaining_length = self.bar_length - filled_length
    
                # 建立進度條
                progress = (self.progress_bars[1] * filled_length + 
                           self.progress_bars[0] * remaining_length)
                await progress_message.edit(content=f"下載進度: {progress} ({current-1}/{total})")

                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                file_path = Path(ydl.prepare_filename(info)).with_suffix('.opus')
                if not file_path.exists():
                    info = await asyncio.to_thread(ydl.extract_info, url, download=True)
                    file_path = Path(ydl.prepare_filename(info)).with_suffix('.opus')

                # 下載完成後更新最終進度
                progress_ratio = current / total
                filled_length = int(self.bar_length * progress_ratio)
                remaining_length = self.bar_length - filled_length
                progress = (self.progress_bars[1] * filled_length + 
                           self.progress_bars[0] * remaining_length)
                await progress_message.edit(content=f"下載進度: {progress} ({current}/{total})")

                return file_path

            data = self.get_guild_data(ctx.guild)
            progress_message = await ctx.followup.send("準備下載中...", ephemeral=True)

            if 'entries' in extracted:
                entries = extracted['entries']
                total_songs = len(entries)

                if total_songs == 1:
                    file_path = await get_or_download(entries[0]['webpage_url'], progress_message, 1, 1)
                    data["play_list"].append(file_path)
                    self.file_usage[str(file_path)] = self.file_usage.get(str(file_path), 0) + 1
                    playlist_info = f"歌曲 {file_path.stem}"
                else:
                    for i, entry in enumerate(entries, 1):
                        file_path = await get_or_download(entry['webpage_url'], progress_message, i, total_songs)
                        data["play_list"].append(file_path)
                        self.file_usage[str(file_path)] = self.file_usage.get(str(file_path), 0) + 1
                    
                        if i == 1:  # 第一首歌開始播放
                            vc = await self.ensure_voice_client(channel, ctx.voice_client)
                            if not vc.is_playing():
                                self.play_next(vc)
                
                    playlist_info = f"{total_songs} 首歌曲"
            else:
                file_path = await get_or_download(search, progress_message, 1, 1)
                data["play_list"].append(file_path)
                self.file_usage[str(file_path)] = self.file_usage.get(str(file_path), 0) + 1
                playlist_info = f"歌曲 {file_path.stem}"

            vc = await self.ensure_voice_client(channel, ctx.voice_client)
            if not vc.is_playing():
                self.play_next(vc)
            
            await progress_message.edit(content=f"已加入 {playlist_info} 到播放列表！")

    @music.command(description="調整播放音量 (0-150%)")
    @discord.option(
        "volume",
        type=discord.SlashCommandOptionType.integer,
        description="音量百分比",
    )
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！", ephemeral=True)
            return
        if volume < 0 or volume > 150:
            await ctx.respond("請輸入 0 到 150 之間的音量百分比！", ephemeral=True)
            return
        data = self.get_guild_data(ctx.guild)
        data["volume"] = volume / 100.0
        if ctx.voice_client.source and isinstance(ctx.voice_client.source, discord.PCMVolumeTransformer):
            ctx.voice_client.source.volume = data["volume"]
        await ctx.respond(f"已將音量調整為 {volume}%！", ephemeral=True)

    @music.command(description="顯示播放清單")
    async def queue(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！", ephemeral=True)
            return
        view = QueueControlView(self, ctx)
        embed = view.build_queue_embed()
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @music.command(escription="暫停音樂")
    async def pause(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！", ephemeral=True)
            return
        vc = ctx.voice_client
        if vc.is_playing():
            vc.pause()
            await ctx.respond("音樂已暫停！", ephemeral=True)
        else:
            await ctx.respond("目前沒有正在播放的音樂！", ephemeral=True)

    @music.command(description="恢復播放音樂")
    async def resume(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！", ephemeral=True)
            return
        vc = ctx.voice_client
        if vc.is_paused():
            vc.resume()
            await ctx.respond("音樂已恢復播放！", ephemeral=True)
        else:
            await ctx.respond("目前音樂沒有暫停！", ephemeral=True)

    @music.command(description="停止播放音樂")
    async def stop(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！", ephemeral=True)
            return
        
        # 找到所有正在進行的下載任務
        data = self.get_guild_data(ctx.guild)
        if data["inactive_task"]:
            data["inactive_task"].cancel()
            data["inactive_task"] = None
        data["play_list"].clear()
    
        # 停止當前播放並斷開連接
        vc = ctx.voice_client
        vc.stop()
        await vc.disconnect()
    
        # 清理暫存檔案
        tmp_path = Path('./tmp')
        if tmp_path.exists():
            for file in tmp_path.iterdir():
                if file.is_file():
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"刪除檔案 {file} 失敗: {e}")
    
        # 取消所有正在進行的下載任務
        try:
            tasks = [task for task in asyncio.all_tasks() 
                    if task.get_name().startswith('yt_dlp_download')]
            for task in tasks:
                task.cancel()
        except Exception as e:
            print(f"取消下載任務失敗: {e}")
        
        await ctx.respond("音樂已停止！", ephemeral=True)
    
    @music.command(description="跳過目前播放的音樂")
    async def skip(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！", ephemeral=True)
            return
        vc = ctx.voice_client
        vc.stop()
        await ctx.respond("已跳過目前播放的音樂！", ephemeral=True)

    @music.command(description="移除指定的歌曲")
    @discord.option(
        "index", 
        type=discord.SlashCommandOptionType.integer, 
        description="歌曲編號"
    )
    async def remove(self, ctx, index: int):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！", ephemeral=True)
            return
        data = self.get_guild_data(ctx.guild)
        if index < 1 or index > len(data["play_list"]):
            await ctx.respond("歌曲編號不正確！", ephemeral=True)
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
        await ctx.respond(f"已移除 {removed_file.name}！", ephemeral=True)

    @music.command(description="隨機播放")
    async def random(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("Bot 未在語音頻道中！", ephemeral=True)
            return
        data = self.get_guild_data(ctx.guild)
        random.shuffle(data["play_list"])
        await ctx.respond("已隨機播放！", ephemeral=True)

    @music.command(description="播放指定的歌曲")
    @discord.option(
        "index", 
        type=discord.SlashCommandOptionType.integer, 
        description="歌曲編號"
    )
    async def play_index(self, ctx, index: int):
        if ctx.author.voice is None:
            await ctx.respond("你必須先加入一個語音頻道！", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        data = self.get_guild_data(ctx.guild)
        vc = await self.ensure_voice_client(channel, ctx.voice_client)
    
        if index < 1 or index > len(data["play_list"]):
            await ctx.respond("歌曲編號不正確！", ephemeral=True)
            return

        if vc.is_playing():
            vc.stop()
            while vc.is_playing():
                await asyncio.sleep(0.1)
    
        data["play_list"].insert(0, data["play_list"].pop(index - 1))
        self.play_next(vc)
        await ctx.respond(f"已播放 {data['current_track'].name}！", ephemeral=True)

class QueueControlView(discord.ui.View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=30)
        self.cog = cog
        self.ctx = ctx
        self.current_page = 0
        self.items_per_page = 10

        # 建立按鈕實例並指定 callback
        self.button_next = discord.ui.Button(label="下一頁", style=discord.ButtonStyle.primary, custom_id="next_page")
        self.button_next.callback = self.next_page_callback

        self.button_prev = discord.ui.Button(label="上一頁", style=discord.ButtonStyle.primary, custom_id="prev_page")
        self.button_prev.callback = self.prev_page_callback

        initial_label = "暫停" if self.ctx.voice_client and self.ctx.voice_client.is_playing() else "播放"
        self.button_toggle = discord.ui.Button(label=initial_label, style=discord.ButtonStyle.primary, custom_id="toggle")
        self.button_toggle.callback = self.toggle_callback

        self.button_skip = discord.ui.Button(label="跳過", style=discord.ButtonStyle.primary, custom_id="skip")
        self.button_skip.callback = self.skip_callback

        self.button_stop = discord.ui.Button(label="終止播放", style=discord.ButtonStyle.danger, custom_id="stop")
        self.button_stop.callback = self.stop_callback

        # 初次建立時更新按鈕（依據頁數決定是否要加入上一頁或下一頁）
        self.update_page_buttons()

    def on_timeout(self):
        self.disable_all_items()
        # 若有原始訊息，可更新 view 來顯示禁用的按鈕
        asyncio.create_task(self.update_view_on_timeout())

    async def update_view_on_timeout(self):
        try:
            await self.ctx.interaction.edit_original_response(view=self)
        except Exception as e:
            print(f"更新 View 失敗: {e}")

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

    def build_queue_embed(self):
        data = self.cog.get_guild_data(self.ctx.guild)
        color = random.randint(0, 16777215)
        embed = discord.Embed(title="播放列表", color=color)
        if data["current_track"] is not None:
            embed.add_field(name="正在播放", value=data["current_track"].stem, inline=False)
        if data["play_list"]:
            playlist = data["play_list"]
            total_pages = (len(playlist) - 1) // self.items_per_page + 1
            if self.current_page >= total_pages:
                self.current_page = total_pages - 1
            start_index = self.current_page * self.items_per_page
            end_index = start_index + self.items_per_page
            page_items = playlist[start_index:end_index]
            playlist_str = ""
            for i, file in enumerate(page_items, start=start_index+1):
                playlist_str += f"{i}. {file.stem}\n"
            embed.add_field(name="即將播放的歌曲", value=playlist_str, inline=False)
            embed.set_footer(text=f"頁數: {self.current_page + 1}/{total_pages}")
        if not embed.fields:
            embed.description = "播放列表是空的！"
        return embed

    def build_queue_embed_with_status(self, status_message: str):
        embed = self.build_queue_embed()
        embed.add_field(name="狀態", value=status_message, inline=False)
        return embed

    def update_page_buttons(self):
        # 先清除所有按鈕
        self.clear_items()
        data = self.cog.get_guild_data(self.ctx.guild)
        total_pages = (len(data["play_list"]) - 1) // self.items_per_page + 1

        # 若不是第一頁則加入上一頁
        if self.current_page > 0:
            self.add_item(self.button_prev)
        # 若不是最後一頁則加入下一頁
        if self.current_page < total_pages - 1:
            self.add_item(self.button_next)
        # 固定加入其他按鈕
        self.add_item(self.button_toggle)
        self.add_item(self.button_skip)
        self.add_item(self.button_stop)

    async def next_page_callback(self, interaction: discord.Interaction):
        if self.ctx.voice_client is None:
            self.disable_all_items()
            embed = self.build_queue_embed_with_status("Bot 未在語音頻道中！")
            await interaction.response.edit_message(embed=embed, view=self)
            return
        data = self.cog.get_guild_data(self.ctx.guild)
        total_pages = (len(data["play_list"]) - 1) // self.items_per_page + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
        self.update_page_buttons()
        embed = self.build_queue_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def prev_page_callback(self, interaction: discord.Interaction):
        if self.ctx.voice_client is None:
            self.disable_all_items()
            embed = self.build_queue_embed_with_status("Bot 未在語音頻道中！")
            await interaction.response.edit_message(embed=embed, view=self)
            return
        if self.current_page > 0:
            self.current_page -= 1
        self.update_page_buttons()
        embed = self.build_queue_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def toggle_callback(self, interaction: discord.Interaction):
        if self.ctx.voice_client is None:
            self.disable_all_items()  # Bot 不在語音頻道，停用所有按鈕
            embed = self.build_queue_embed_with_status("Bot 未在語音頻道中！")
            await interaction.response.edit_message(embed=embed, view=self)
            return
        vc = self.ctx.voice_client
        if vc.is_playing():
            vc.pause()
            status = "音樂已暫停！"
            self.button_toggle.label = "播放"
        elif vc.is_paused():
            vc.resume()
            status = "音樂已恢復播放！"
            self.button_toggle.label = "暫停"
        else:
            status = "目前沒有正在播放的音樂！"
        self.update_page_buttons()  # 重新更新按鈕
        embed = self.build_queue_embed_with_status(status)
        await interaction.response.edit_message(embed=embed, view=self)

    async def skip_callback(self, interaction: discord.Interaction):
        if self.ctx.voice_client is None:
            self.disable_all_items()
            embed = self.build_queue_embed_with_status("Bot 未在語音頻道中！")
            await interaction.response.edit_message(embed=embed, view=self)
            return
        vc = self.ctx.voice_client
        vc.stop()
        embed = self.build_queue_embed_with_status("已跳過目前播放的音樂！")
        await interaction.response.edit_message(embed=embed, view=self)

    async def stop_callback(self, interaction: discord.Interaction):
        if self.ctx.voice_client is None:
            self.disable_all_items()
            embed = self.build_queue_embed_with_status("Bot 未在語音頻道中！")
            await interaction.response.edit_message(embed=embed, view=self)
            return

        # 找到所有正在進行的下載任務
        data = self.cog.get_guild_data(self.ctx.guild)
    
        # 取消計時器
        if data["inactive_task"]:
            data["inactive_task"].cancel()
            data["inactive_task"] = None
    
        # 清空播放列表
        data["play_list"].clear()

        # 停止當前播放並斷開連接
        vc = self.ctx.voice_client
        vc.stop()
        await vc.disconnect()

        # 清理暫存檔案
        tmp_path = Path('./tmp')
        if tmp_path.exists():
            for file in tmp_path.iterdir():
                if file.is_file():
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"刪除檔案 {file} 失敗: {e}")

        # 取消所有正在進行的下載任務
        try:
            tasks = [task for task in asyncio.all_tasks() 
                    if task.get_name().startswith('yt_dlp_download')]
            for task in tasks:
                task.cancel()
        except Exception as e:
            print(f"取消下載任務失敗: {e}")

        self.disable_all_items()
        embed = self.build_queue_embed_with_status("音樂已停止！")
        await interaction.response.edit_message(embed=embed, view=self)

def setup(bot):
    bot.add_cog(Music(bot))