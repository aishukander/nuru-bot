import discord
import asyncio
from discord.ext import commands
import tomllib
import tomli_w
from pathlib import Path
from functools import wraps

toml_dir = Path(__file__).resolve().parents[1] / "toml"

class Channel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channel_set = set()
        self.origin_channels = self.load_origin_channels()

    @staticmethod
    def guild_admin_examine(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            try:
                if ctx.author.guild_permissions.administrator:
                    return await func(self, ctx, *args, **kwargs)
                await ctx.respond("你沒有管理者權限用來執行這個指令", ephemeral=True)
            except AttributeError:
                await ctx.respond("你不在伺服器內", ephemeral=True)
        return wrapper

    def load_dynamic_voice_data(self):
        try:
            with open(toml_dir / "DynamicVoice.toml", "rb") as tfile:
                return tomllib.load(tfile)
        except FileNotFoundError:
            return {"ID": {}, "Name": {}}

    def load_origin_channels(self):
        data = self.load_dynamic_voice_data()
        return data.get("ID", {})

    def load_dynamic_voice_name(self):
        data = self.load_dynamic_voice_data()
        return data.get("Name", {})

    def save_dynamic_voice_data(self, origin_channels: dict, dynamic_voice_names: dict):
        data = {
            "ID": origin_channels,
            "Name": dynamic_voice_names
        }
        with open(toml_dir / "DynamicVoice.toml", "wb") as f:
            tomli_w.dump(data, f)

    def save_origin_channels(self, origin_channels: dict):
        dynamic_voice_names = self.load_dynamic_voice_name()
        self.save_dynamic_voice_data(origin_channels, dynamic_voice_names)

    def dump_dynamic_voice_name(self, dynamic_voice_name: dict):
        origin_channels = self.load_origin_channels()
        self.save_dynamic_voice_data(origin_channels, dynamic_voice_name)

    def get_dynamic_voice_channel_names(ctx: discord.AutocompleteContext):
        try:
            with open(toml_dir / "DynamicVoice.toml", "rb") as tfile:
                origin_channels = tomllib.load(tfile).get("ID", {})
        except FileNotFoundError:
            origin_channels = {}

        query = ctx.value.lower()
        guild_id = str(ctx.interaction.guild.id)
        choices = []
        if guild_id in origin_channels:
            for cid in origin_channels[guild_id]:
                ch = ctx.interaction.client.get_channel(cid)
                if ch and ch.name.lower().startswith(query):
                    choices.append(discord.OptionChoice(name=ch.name, value=ch.name))
        return choices

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild_id = str(member.guild.id)
        if guild_id not in self.origin_channels:
            return

        for parent_id in self.origin_channels[guild_id]:
            # 使用者進入母頻道，建立副本
            if after.channel and after.channel.id == parent_id:
                dynamic_names = self.load_dynamic_voice_name()
                key = f"{guild_id}_{parent_id}"
                template = dynamic_names.get(key, "{}的動態語音")
                try:
                    new_ch = await after.channel.clone(name=template.format(member.display_name))
                except (discord.Forbidden, discord.HTTPException):
                    new_ch = await after.channel.clone(name=f"{member.display_name}的動態語音")
                await member.move_to(new_ch)
                self.voice_channel_set.add(new_ch.id)

            # 空頻道移除
            elif before.channel and before.channel.id in self.voice_channel_set and len(before.channel.members) == 0:
                try:
                    await before.channel.delete(reason="Delete empty voice channel")
                    self.voice_channel_set.remove(before.channel.id)
                except (discord.Forbidden, discord.HTTPException):
                    pass

    dynamic_voice = discord.SlashCommandGroup("dynamic_voice", "動態語音命令群組")

    @dynamic_voice.command(description="新增動態語音母頻道")
    @discord.option("name", str, description="母頻道名稱")
    @guild_admin_examine
    async def add_voice(self, ctx: discord.ApplicationContext, name: str):
        guild_id = str(ctx.guild.id)
        try:
            channel = await ctx.guild.create_voice_channel(name)
            self.origin_channels.setdefault(guild_id, []).append(channel.id)
            self.save_origin_channels(self.origin_channels)
            await ctx.respond(f"動態語音母頻道 [{channel.name}] 已建立", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("機器人缺少建立語音頻道的權限", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.respond(f"建立失敗: {e}", ephemeral=True)

    @dynamic_voice.command(description="移除動態語音母頻道")
    @discord.option("name", str, description="母頻道名稱", autocomplete=get_dynamic_voice_channel_names)
    @guild_admin_examine
    async def remove_voice(self, ctx: discord.ApplicationContext, name: str):
        guild_id = str(ctx.guild.id)
        channels = self.origin_channels.get(guild_id, [])
        if not channels:
            await ctx.respond("此伺服器未設定動態語音", ephemeral=True)
            return

        for idx, pid in enumerate(channels):
            ch = self.bot.get_channel(pid)
            if ch and ch.name == name:
                try:
                    await ch.delete()
                except (discord.Forbidden, discord.HTTPException) as e:
                    await ctx.respond(f"刪除母頻道失敗: {e}", ephemeral=True)
                    return
                channels.pop(idx)
                if not channels:
                    self.origin_channels.pop(guild_id)
                self.save_origin_channels(self.origin_channels)
                dyn_names = self.load_dynamic_voice_name()
                key = f"{guild_id}_{pid}"
                if key in dyn_names:
                    dyn_names.pop(key)
                    self.dump_dynamic_voice_name(dyn_names)
                await ctx.respond(f"動態語音母頻道 [{name}] 已移除", ephemeral=True)
                return

        await ctx.respond(f"未找到母頻道 [{name}]", ephemeral=True)

    @dynamic_voice.command(description="設定子頻道名稱範本")
    @discord.option("parent_channel_name", str, description="母頻道名稱", autocomplete=get_dynamic_voice_channel_names)
    @discord.option("new_voice_name", str, description="新的子頻道名稱範本，{} 代表使用者名稱")
    @guild_admin_examine
    async def set_voice_template(self, ctx: discord.ApplicationContext, parent_channel_name: str, new_voice_name: str):
        parent = discord.utils.get(ctx.guild.voice_channels, name=parent_channel_name)
        if not parent:
            await ctx.respond(f"找不到母頻道 [{parent_channel_name}]", ephemeral=True)
            return

        dyn_names = self.load_dynamic_voice_name()
        key = f"{ctx.guild.id}_{parent.id}"
        dyn_names[key] = new_voice_name
        self.dump_dynamic_voice_name(dyn_names)
        await ctx.respond(f"已更新 [{parent_channel_name}] 的子頻道名稱範本為 「{new_voice_name}」", ephemeral=True)

    @commands.slash_command(description="將語音頻道內所有人移動到另一頻道")
    @discord.option("source", discord.SlashCommandOptionType.channel, description="來源頻道", channel_types=[discord.ChannelType.voice])
    @discord.option("target", discord.SlashCommandOptionType.channel, description="目標頻道", channel_types=[discord.ChannelType.voice])
    async def move_voice(self, ctx: discord.ApplicationContext, source: discord.VoiceChannel, target: discord.VoiceChannel):
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("你沒有管理者權限用於此指令", ephemeral=True)
            return

        if not source.members:
            await ctx.respond(f"[{source.name}] 目前沒有人在裡面", ephemeral=True)
            return

        try:
            await asyncio.gather(*[m.move_to(target) for m in source.members])
            await ctx.respond(f"已將 [{source.name}] 的所有人移動到 [{target.name}]", ephemeral=True)
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.respond(f"移動失敗: {e}", ephemeral=True)

    @commands.slash_command(description="建立身分組並創建對應文字/語音頻道")
    @discord.option("name", str, description="身分組名稱")
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
            await ctx.respond(f"身分組與頻道 [{name}] 已建立", ephemeral=True)
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.respond(f"建立失敗: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(Channel(bot))