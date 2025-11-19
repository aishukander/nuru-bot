import discord
from discord.ext import commands
from pathlib import Path
from ytmusicapi import YTMusic
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

        self.default_volume = float(self.Setting["Volume"].rstrip('%')) / 100
        self.inactive_timeout = int(self.Setting["Inactive_Timeout"]) # channel inactivity timeout in seconds
        self.guild_data = {}  # guild_id -> {"play_list": [], "current_track": None, "volume": <float>, "inactive_task": None}
        self.debounce_tasks = {} # (user_id, channel_id) -> asyncio.Task
        
        # https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#video-format-options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
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

    async def play_next(self, vc):
        server = self.get_guild_data(vc.guild)
        # Reset inactivity timer
        if server["inactive_task"]:
            server["inactive_task"].cancel()
        server["inactive_task"] = asyncio.create_task(
            self.check_inactivity(vc.guild.id)
        )

        if vc.is_playing():
            return

        if server["play_list"]:
            next_song = server["play_list"].pop(0)
            server["current_track"] = next_song
            
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info_dict = ydl.extract_info(next_song['url'], download=False)
                    audio_url = None
                    for f in info_dict.get('formats', []):
                        if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                            audio_url = f['url']
                            break
                    if not audio_url:
                        audio_url = info_dict['url']

                source = discord.FFmpegPCMAudio(audio_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
                transformer = discord.PCMVolumeTransformer(source, volume=server["volume"])

                def after_playing(error):
                    if error:
                        print(f"播放時發生錯誤: {error}")
                    server["current_track"] = None
                    asyncio.run_coroutine_threadsafe(self.play_next(vc), self.bot.loop)

                vc.play(transformer, after=after_playing)

            except Exception as e:
                print(f"準備播放時發生錯誤: {e}")
                await asyncio.sleep(0.5)
                await self.play_next(vc)
        else:
            server["current_track"] = None
            # Reset inactivity timer if no songs left
            if server["inactive_task"]:
                server["inactive_task"].cancel()
            server["inactive_task"] = asyncio.create_task(
                self.check_inactivity(vc.guild.id)
            )

    # Music search autocomplete
    async def get_music_names(self, ctx: discord.AutocompleteContext):
        interaction_key = (ctx.interaction.user.id, ctx.interaction.channel_id)

        # Cancel any existing debounce task for this user/channel
        if interaction_key in self.debounce_tasks:
            self.debounce_tasks[interaction_key].cancel()

        # Create a new task to perform the search after a delay
        new_task = asyncio.create_task(self._debounced_search(ctx))
        self.debounce_tasks[interaction_key] = new_task

        try:
            # Wait for the debounced task to complete
            results = await new_task
            return results
        except asyncio.CancelledError:
            # This is expected if the user is still typing
            return []
        finally:
            # Clean up the task from the dictionary
            if interaction_key in self.debounce_tasks and self.debounce_tasks[interaction_key] is new_task:
                del self.debounce_tasks[interaction_key]

    async def _debounced_search(self, ctx: discord.AutocompleteContext):
        await asyncio.sleep(0.2)  # Debounce delay

        query = ctx.value
        if not query or query.strip() == "":
            return []
        if query.startswith("http://") or query.startswith("https://"):
            return []

        try:
            results = await asyncio.to_thread(YTMusic().search, query, filter="songs")
            results = results[:int(self.Setting["Search_Length"])]
            seen = set()
            options = []
            for entry in results:
                title = entry.get("title")
                artists = ", ".join(a["name"] for a in entry.get("artists", [])) if entry.get("artists") else ""
                display = (f"{title} - {artists}" if artists else title)[:100]
                # Avoid duplicate displays
                if display and display not in seen:
                    seen.add(display)
                    value = entry.get("videoId") or title
                    options.append(discord.OptionChoice(name=display, value=value))
            return options
        except Exception as e:
            print(f"Error during music search: {e}")
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

        if not (search.startswith("http://") or search.startswith("https://")):
            search = "ytsearch:" + search

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            extracted = await asyncio.to_thread(ydl.extract_info, search, download=False)

            data = self.get_guild_data(ctx.guild)
            
            if 'entries' in extracted:
                entries = extracted['entries']
                for entry in entries:
                    song = {'title': entry.get('title', 'Unknown Title'), 'url': entry.get('webpage_url')}
                    data["play_list"].append(song)
                playlist_info = f"{len(entries)} 首歌曲"
            else:
                song = {'title': extracted.get('title', 'Unknown Title'), 'url': extracted.get('webpage_url')}
                data["play_list"].append(song)
                playlist_info = f"歌曲 {song['title']}"

            vc = await self.ensure_voice_client(channel, ctx.voice_client)
            if not vc.is_playing():
                asyncio.create_task(self.play_next(vc))
            
            await ctx.followup.send(f"已加入 {playlist_info} 到播放列表！", ephemeral=True)

    @music.command(description="調整播放音量 (0-150)")
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
        
        data = self.get_guild_data(ctx.guild)
        if data["inactive_task"]:
            data["inactive_task"].cancel()
            data["inactive_task"] = None
        data["play_list"].clear()
    
        vc = ctx.voice_client
        vc.stop()
        await vc.disconnect()
        
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
        removed_song = data["play_list"].pop(index-1)
        await ctx.respond(f"已移除 {removed_song['title']}！", ephemeral=True)

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
        asyncio.create_task(self.play_next(vc))
        await ctx.respond(f"已播放 {data['current_track']['title']}！", ephemeral=True)

class QueueControlView(discord.ui.View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=30)
        self.cog = cog
        self.ctx = ctx
        self.current_page = 0
        self.items_per_page = 10

        # Create button instances and assign callbacks
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

        # Add buttons to the view
        self.update_page_buttons()

    def on_timeout(self):
        self.disable_all_items()
        # If there is an original message, update the view to show the disabled buttons
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
            embed.add_field(name="正在播放", value=data["current_track"]['title'], inline=False)
        if data["play_list"]:
            playlist = data["play_list"]
            total_pages = (len(playlist) - 1) // self.items_per_page + 1
            if self.current_page >= total_pages:
                self.current_page = total_pages - 1
            start_index = self.current_page * self.items_per_page
            end_index = start_index + self.items_per_page
            page_items = playlist[start_index:end_index]
            playlist_str = ""
            for i, song in enumerate(page_items, start=start_index+1):
                playlist_str += f"{i}. {song['title']}\n"
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
        # Clear all buttons first
        self.clear_items()
        data = self.cog.get_guild_data(self.ctx.guild)
        total_pages = (len(data["play_list"]) - 1) // self.items_per_page + 1

        # If not the first page, add the previous page button
        if self.current_page > 0:
            self.add_item(self.button_prev)
        # If not the last page, add the next page button
        if self.current_page < total_pages - 1:
            self.add_item(self.button_next)
        # Add the toggle, skip, and stop buttons
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
        # Check if the bot is connected to a voice channel
        if self.ctx.voice_client is None:
            self.disable_all_items()
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
        self.update_page_buttons()  # Update buttons after toggling
        embed = self.build_queue_embed_with_status(status)
        await interaction.response.edit_message(embed=embed, view=self)

    async def skip_callback(self, interaction: discord.Interaction):
        if self.ctx.voice_client is None:
            self.disable_all_items()
            embed = self.build_queue_embed_with_status("Bot 未在語音頻道中！")
            await interaction.response.edit_message(embed=embed, view=self)
            return

        vc = self.ctx.voice_client
        data = self.cog.get_guild_data(self.ctx.guild)
        old_track = data.get("current_track")

        async def wait_for_track_change(old_track_to_check):
            while self.cog.get_guild_data(self.ctx.guild).get("current_track") == old_track_to_check:
                await asyncio.sleep(0.1)

        vc.stop()
        try:
            await asyncio.wait_for(wait_for_track_change(old_track), timeout=5.0)
        except asyncio.TimeoutError:
            pass

        embed = self.build_queue_embed_with_status("已跳過目前播放的音樂！")
        await interaction.response.edit_message(embed=embed, view=self)

    async def stop_callback(self, interaction: discord.Interaction):
        if self.ctx.voice_client is None:
            self.disable_all_items()
            embed = self.build_queue_embed_with_status("Bot 未在語音頻道中！")
            await interaction.response.edit_message(embed=embed, view=self)
            return

        data = self.cog.get_guild_data(self.ctx.guild)

        if data["inactive_task"]:
            data["inactive_task"].cancel()
            data["inactive_task"] = None

        data["play_list"].clear()

        vc = self.ctx.voice_client
        vc.stop()
        await vc.disconnect()

        self.disable_all_items()
        embed = self.build_queue_embed_with_status("音樂已停止！")
        await interaction.response.edit_message(embed=embed, view=self)

def setup(bot):
    bot.add_cog(Music(bot))