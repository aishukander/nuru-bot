import discord
import asyncio
from discord.ext import commands
import json
from pathlib import Path

json_dir = Path(__file__).resolve().parents[1] / "json"

class Channel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.voice_channel_set = set()
        with open(json_dir / "DynamicVoiceID.json", "r", encoding="utf8") as jfile:
            self.origin_channels = json.load(jfile) 

    def LoadDynamicVoiceName(self):
        with open(json_dir / "DynamicVoiceName.json", "r", encoding="utf8") as jfile:
            return json.load(jfile)
        
    def DumpDynamicVoiceName(self, DynamicVoiceName):
        with open(json_dir / "DynamicVoiceName.json", "w", encoding="utf8") as f:
            json.dump(DynamicVoiceName, f, indent=4)
        
    def SaveDynamicVoice_ID_json(self, origin_channels):
        json_str = "{}" if not origin_channels else "{" + ",".join(
        f'\n"{guild_id}": {channel_ids}' for guild_id, channel_ids in origin_channels.items()) + "\n}"
        with open(json_dir / "DynamicVoiceID.json", "w", encoding="utf8") as f:
            f.write(json_str)

    @commands.Cog.listener() 
    async def on_voice_state_update(self, member, before, after):
        guild_id = str(member.guild.id)
        if guild_id not in self.origin_channels:
            return

        for parent_channel_id in self.origin_channels[guild_id]:
            if after.channel and after.channel.id == parent_channel_id:
                try:
                    DynamicVoiceName = self.LoadDynamicVoiceName()
                    new_channel = await after.channel.clone(name=DynamicVoiceName[f"{guild_id}_{parent_channel_id}"].format(member.display_name))
                except:
                    new_channel = await after.channel.clone(name=f"{member.display_name}的動態語音")
                await member.move_to(new_channel)
                self.voice_channel_set.add(new_channel.id)
            elif before.channel and before.channel.id in self.voice_channel_set and len(before.channel.members) == 0:
                await before.channel.delete(reason="Delete empty voice channel")
                self.voice_channel_set.remove(before.channel.id)

    dynamic_voice = discord.SlashCommandGroup("dynamic_voice", "dynamic_voice command group")

    @dynamic_voice.command(description="管理動態語音頻道")
    @discord.option("action", type=discord.SlashCommandOptionType.string, description="add/remove", choices=["add", "remove"])
    @discord.option("name", type=discord.SlashCommandOptionType.string, description="母頻道名稱")
    async def management(self, ctx, action: str, name: str):
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("你沒有管理者權限用來執行這個指令")
            return

        guild_id = str(ctx.guild.id)
        if action.lower() == "add":
            try:
                channel = await ctx.guild.create_voice_channel(name)
                self.origin_channels.setdefault(guild_id, []).append(channel.id)
                self.SaveDynamicVoice_ID_json(self.origin_channels)
                await ctx.respond(f"動態語音 {channel.name} 已建立")
            except discord.Forbidden:
                await ctx.respond("機器人缺少創建語音頻道的權限")
        elif action.lower() == "remove":
            channels = self.origin_channels.get(guild_id)
            if not channels:
                await ctx.respond("此伺服器未設定動態語音")
                return

            for idx, parent_channel_id in enumerate(channels):
                channel = self.bot.get_channel(parent_channel_id)
                if channel.name == name:
                    await channel.delete()
                    del self.origin_channels[guild_id][idx]
                    if not self.origin_channels[guild_id]:
                        self.origin_channels.pop(guild_id)
                    self.SaveDynamicVoice_ID_json(self.origin_channels)
                    try:
                        DynamicVoiceName = self.LoadDynamicVoiceName()
                        del DynamicVoiceName[f"{guild_id}_{parent_channel_id}"]
                        self.DumpDynamicVoiceName(DynamicVoiceName)
                        await ctx.respond(f"動態語音 {name} 已刪除")
                    except:
                        await ctx.respond("動態語音已刪除")
                    return
            await ctx.respond(f"未找到 {name} 動態語音")
        else:
            await ctx.respond("請輸入正確的動作(add/remove)")

    @dynamic_voice.command(description="更新動態語音子頻道名稱")
    @discord.option("parent_channel_name", type=discord.SlashCommandOptionType.string, description="母頻道名稱")
    @discord.option("new_voice_name", type=discord.SlashCommandOptionType.string, description="新的子頻道名稱(可以用{}代表第一個進入語音的使用者)")
    async def update_voice_name(self, ctx, parent_channel_name, new_voice_name):
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("你沒有管理者權限用來執行這個指令")
            return

        DynamicVoiceName = self.LoadDynamicVoiceName()
        parent_channel = discord.utils.get(ctx.guild.voice_channels, name=parent_channel_name)
        if not parent_channel:
            await ctx.respond(f'未找到名為 {parent_channel_name} 的母頻道')
            return

        DynamicVoiceName[f'{ctx.guild.id}_{parent_channel.id}'] = new_voice_name
        self.DumpDynamicVoiceName(DynamicVoiceName)
        await ctx.respond(f'已將 {parent_channel_name} 的子頻道名稱更新為 {new_voice_name}')

    @commands.slash_command(description="將語音頻道內所有人移動到另一個語音頻道")
    @discord.option("source", type=discord.SlashCommandOptionType.channel, description="源頻道", channel_types=[discord.ChannelType.voice])
    @discord.option("target", type=discord.SlashCommandOptionType.channel, description="目標頻道", channel_types=[discord.ChannelType.voice])
    async def move_voice(self, ctx, source: discord.VoiceChannel, target: discord.VoiceChannel):
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond("你沒有管理者權限用來執行這個指令")
            return

        if not source.members:
            await ctx.respond(f"[{source.name}] 沒有人在裡面")
            return

        await asyncio.gather(*[member.move_to(target) for member in source.members])
        await ctx.respond(f"已將 [{source.name}] 的所有人移動到 [{target.name}]")

    @commands.slash_command(description="創建身分組並且添加文字和語音頻道")
    @discord.option("name", type=discord.SlashCommandOptionType.string, description="身分組名稱")
    async def create_role(self, ctx, name: str):
        guild = ctx.guild
        role = await guild.create_role(name=name)
        category = await guild.create_category(name)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            role: discord.PermissionOverwrite(read_messages=True),
        }
        await category.create_text_channel(name, overwrites=overwrites)
        await category.create_voice_channel(name, overwrites=overwrites)
        await ctx.respond("完成")

def setup(bot):
    bot.add_cog(Channel(bot))