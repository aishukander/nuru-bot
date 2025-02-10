import discord
import asyncio
from discord.ext import commands
import json
from pathlib import Path

json_dir = Path(__file__).resolve().parents[1] / "json"

class Channel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_channel_set = set()
        self.origin_channels = self.load_origin_channels()

    def load_origin_channels(self) -> dict:
        try:
            with open(json_dir / "DynamicVoiceID.json", "r", encoding="utf8") as jfile:
                return json.load(jfile)
        except FileNotFoundError:
            return {}

    def load_dynamic_voice_name(self) -> dict:
        try:
            with open(json_dir / "DynamicVoiceName.json", "r", encoding="utf8") as jfile:
                return json.load(jfile)
        except FileNotFoundError:
            return {}

    def dump_dynamic_voice_name(self, dynamic_voice_name: dict) -> None:
        with open(json_dir / "DynamicVoiceName.json", "w", encoding="utf8") as f:
            json.dump(dynamic_voice_name, f, indent=4, ensure_ascii=False)

    def save_origin_channels(self, origin_channels: dict) -> None:
        with open(json_dir / "DynamicVoiceID.json", "w", encoding="utf8") as f:
            json.dump(origin_channels, f, indent=4, ensure_ascii=False)

    def get_dynamic_voice_channel_names(ctx: discord.AutocompleteContext):
        with open(json_dir / "DynamicVoiceID.json", "r", encoding="utf8") as jfile:
            origin_channels = json.load(jfile)

        query = ctx.value.lower()
        guild = ctx.interaction.guild
        guild_id = str(guild.id)
        channel_names = []
        if guild_id in origin_channels:
            for channel_id in origin_channels[guild_id]:
                channel = ctx.interaction.client.get_channel(channel_id)
                if channel:
                    channel_names.append(channel.name)
        return [
            discord.OptionChoice(name=pic, value=pic)
            for pic in channel_names
            if pic.lower().startswith(query)
        ]

    @commands.Cog.listener() 
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild_id = str(member.guild.id)
        if guild_id not in self.origin_channels:
            return

        for parent_channel_id in self.origin_channels[guild_id]:
            if after.channel and after.channel.id == parent_channel_id:
                dynamic_voice_name = self.load_dynamic_voice_name()
                key = f"{guild_id}_{parent_channel_id}"
                channel_name = dynamic_voice_name.get(key, "{}的動態語音")
                try:
                    new_channel = await after.channel.clone(name=channel_name.format(member.display_name))
                except (discord.Forbidden, discord.HTTPException):
                    new_channel = await after.channel.clone(name=f"{member.display_name}的動態語音")
                await member.move_to(new_channel)
                self.voice_channel_set.add(new_channel.id)
            elif before.channel and before.channel.id in self.voice_channel_set and len(before.channel.members) == 0:
                try:
                    await before.channel.delete(reason="Delete empty voice channel")
                    self.voice_channel_set.remove(before.channel.id)
                except (discord.Forbidden, discord.HTTPException):
                    pass

    dynamic_voice = discord.SlashCommandGroup("dynamic_voice", "dynamic_voice command group")

    @dynamic_voice.command(
        description="新增動態語音頻道"
    )
    @discord.option(
        "name", 
        type=discord.SlashCommandOptionType.string, 
        description="母頻道名稱"
    )
    async def add_voice(self, ctx: discord.ApplicationContext, name: str):
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("你沒有管理者權限用來執行這個指令")
            return

        guild_id = str(ctx.guild.id)
        try:
            channel = await ctx.guild.create_voice_channel(name)
            self.origin_channels.setdefault(guild_id, []).append(channel.id)
            self.save_origin_channels(self.origin_channels)
            await ctx.respond(f"動態語音 {channel.name} 已建立")
        except discord.Forbidden:
            await ctx.respond("機器人缺少創建語音頻道的權限")
        except discord.HTTPException as e:
            await ctx.respond(f"建立失敗: {e}")

    @dynamic_voice.command(
        description="移除動態語音頻道"
    )
    @discord.option(
        "name", 
        type=discord.SlashCommandOptionType.string, 
        description="母頻道名稱",
        autocomplete=get_dynamic_voice_channel_names
    )
    async def remove_voice(self, ctx: discord.ApplicationContext, name: str):
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("你沒有管理者權限用來執行這個指令")
            return

        guild_id = str(ctx.guild.id)
        channels = self.origin_channels.get(guild_id)
        if not channels:
            await ctx.respond("此伺服器未設定動態語音")
            return

        for idx, parent_channel_id in enumerate(channels):
            channel = self.bot.get_channel(parent_channel_id)
            if channel and channel.name == name:
                try:
                    await channel.delete()
                except (discord.Forbidden, discord.HTTPException) as e:
                    await ctx.respond(f"刪除頻道失敗: {e}")
                    return
                del self.origin_channels[guild_id][idx]
                if not self.origin_channels[guild_id]:
                    self.origin_channels.pop(guild_id)
                self.save_origin_channels(self.origin_channels)
                dynamic_voice_name = self.load_dynamic_voice_name()
                key = f"{guild_id}_{parent_channel_id}"
                if key in dynamic_voice_name:
                    dynamic_voice_name.pop(key)
                    self.dump_dynamic_voice_name(dynamic_voice_name)
                await ctx.respond(f"動態語音 {name} 已刪除")
                return
        await ctx.respond(f"未找到 {name} 動態語音")

    @dynamic_voice.command(
        description="更新動態語音子頻道名稱"
    )
    @discord.option(
        "parent_channel_name", 
        type=discord.SlashCommandOptionType.string, 
        description="母頻道名稱",
        autocomplete=get_dynamic_voice_channel_names
    )
    @discord.option(
        "new_voice_name", 
        type=discord.SlashCommandOptionType.string, 
        description="新的子頻道名稱(可以用{}代表第一個進入語音的使用者)"
    )
    async def set_voice_template(self, ctx: discord.ApplicationContext, parent_channel_name: str, new_voice_name: str):
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("你沒有管理者權限用來執行這個指令")
            return

        dynamic_voice_name = self.load_dynamic_voice_name()
        parent_channel = discord.utils.get(ctx.guild.voice_channels, name=parent_channel_name)
        if not parent_channel:
            await ctx.respond(f'未找到名為 {parent_channel_name} 的母頻道')
            return

        key = f'{ctx.guild.id}_{parent_channel.id}'
        dynamic_voice_name[key] = new_voice_name
        self.dump_dynamic_voice_name(dynamic_voice_name)
        await ctx.respond(f'已將 {parent_channel_name} 的子頻道名稱更新為 {new_voice_name}')

    @commands.slash_command(
        description="將語音頻道內所有人移動到另一個語音頻道"
    )
    @discord.option(
        "source", 
        type=discord.SlashCommandOptionType.channel, 
        description="源頻道", 
        channel_types=[discord.ChannelType.voice]
    )
    @discord.option(
        "target", 
        type=discord.SlashCommandOptionType.channel, 
        description="目標頻道", 
        channel_types=[discord.ChannelType.voice]
    )
    async def move_voice(self, ctx: discord.ApplicationContext, source: discord.VoiceChannel, target: discord.VoiceChannel):
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("你沒有管理者權限用來執行這個指令")
            return

        if not source.members:
            await ctx.respond(f"[{source.name}] 沒有人在裡面")
            return

        try:
            await asyncio.gather(*[member.move_to(target) for member in source.members])
            await ctx.respond(f"已將 [{source.name}] 的所有人移動到 [{target.name}]")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.respond(f"移動失敗: {e}")

    @commands.slash_command(
        description="創建身分組並且添加文字和語音頻道"
    )
    @discord.option(
        "name", 
        type=discord.SlashCommandOptionType.string, 
        description="身分組名稱"
    )
    async def create_role(self, ctx: discord.ApplicationContext, name: str):
        guild = ctx.guild
        try:
            role = await guild.create_role(name=name)
            category = await guild.create_category(name)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role: discord.PermissionOverwrite(read_messages=True),
            }
            await category.create_text_channel(name, overwrites=overwrites)
            await category.create_voice_channel(name, overwrites=overwrites)
            await ctx.respond("完成")
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.respond(f"創建失敗: {e}")

def setup(bot: commands.Bot):
    bot.add_cog(Channel(bot))