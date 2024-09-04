import discord
import asyncio
from discord.ext import commands
import modules.json
from modules.json import DynamicVoice_ID_json_path, DynamicVoice_Name_json_path

class Channel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.voice_channel_set = set()
        self.origin_channels = modules.json.open_json(DynamicVoice_ID_json_path)

    @commands.Cog.listener() 
    async def on_voice_state_update(self, member, before, after):

        guild_id = str(member.guild.id)

        if guild_id not in self.origin_channels:
            return

        self.origin_channels_for_guild = self.origin_channels[guild_id]

        for parent_channel_id in self.origin_channels_for_guild:
            if after.channel and after.channel.id == parent_channel_id:
                try:
                    DynamicVoiceName = modules.json.open_json(DynamicVoice_Name_json_path)
                    new_channel = await after.channel.clone(name=DynamicVoiceName[f"{guild_id}_{parent_channel_id}"].format(member.display_name))
                except:
                    new_channel = await after.channel.clone(name=f"{member.display_name}的動態語音")
        
                await member.move_to(new_channel)
        
                self.voice_channel_set.add(new_channel.id)
        
            elif before.channel and before.channel.id in self.voice_channel_set:
                if len(before.channel.members) == 0: 
                    await before.channel.delete(reason="Delete empty voice channel")
                    self.voice_channel_set.remove(before.channel.id)

    dynamic_voice = discord.SlashCommandGroup("dynamic_voice", "dynamic_voice command group")

    @dynamic_voice.command(description="管理動態語音頻道")
    @discord.option("action", type=discord.SlashCommandOptionType.string, description="add/remove")
    @discord.option("name", type=discord.SlashCommandOptionType.string, description="母頻道名稱")
    async def management(self, ctx, action: str, name: str):
        if ctx.author.guild_permissions.administrator:
            guild_id = str(ctx.guild.id)

            if action.lower() == "add":
                channel = await ctx.guild.create_voice_channel(name)
        
                if guild_id not in self.origin_channels:
                    self.origin_channels[guild_id] = []
            
                self.origin_channels[guild_id].append(channel.id)

                modules.json.save_DynamicVoice_ID_json(self.origin_channels)
                await ctx.respond(f"動態語音 {channel.name} 已建立")

            elif action.lower() == "remove":
                channels = self.origin_channels.get(guild_id)
                if not channels:
                    return await ctx.respond("此伺服器未設定動態語音")

                for idx, parent_channel_id in enumerate(channels):
            
                    channel = self.bot.get_channel(parent_channel_id)
                    if channel.name == name:
                
                        await channel.delete()
                
                        del self.origin_channels[guild_id][idx]  
                        if not self.origin_channels[guild_id]:
                            self.origin_channels.pop(guild_id)

                        modules.json.save_DynamicVoice_ID_json(self.origin_channels)

                        try:
                            DynamicVoiceName = modules.json.open_json(DynamicVoice_Name_json_path)

                            del DynamicVoiceName[f"{guild_id}_{parent_channel_id}"]

                            modules.json.dump_json(DynamicVoice_Name_json_path, DynamicVoiceName, 4)
                        
                            await ctx.respond(f"動態語音 {name} 已刪除")
                        except:
                            await ctx.respond("動態語音已刪除")

                        return

                await ctx.respond(f"未找到 {name} 動態語音")
            else:
                await ctx.respond("請輸入正確的動作(add/remove)")
        else:
            await ctx.respond("你沒有管理者權限用來執行這個指令")

    @dynamic_voice.command(description="更新動態語音子頻道名稱")
    @discord.option("parent_channel_name", type=discord.SlashCommandOptionType.string, description="母頻道名稱")
    @discord.option("new_voice_name", type=discord.SlashCommandOptionType.string, description="新的子頻道名稱(可以用{}代表第一個進入語音的使用者)")
    async def update_voice_name(self, ctx,parent_channel_name, new_voice_name):
        if ctx.author.guild_permissions.administrator:
            # 讀取 DynamicVoiceName.json 文件
            DynamicVoiceName = modules.json.open_json(DynamicVoice_Name_json_path)

            # 尋找匹配的語音頻道
            parent_channel = None
            for channel in ctx.guild.voice_channels:
                if channel.name == parent_channel_name:
                    parent_channel = channel
                    break

            # 檢查是否找到匹配的頻道
            if parent_channel is None:
                await ctx.respond(f'未找到名為 {parent_channel_name} 的母頻道')
                return

            # 更新 VoiceName 的值
            DynamicVoiceName[f'{ctx.guild.id}_{parent_channel.id}'] = new_voice_name

            # 將更新後的設定寫回 DynamicVoiceName.json 文件
            modules.json.dump_json(DynamicVoice_Name_json_path, DynamicVoiceName, 4)

            await ctx.respond(f'已將 {parent_channel_name} 的子頻道名稱更新為 {new_voice_name}')
        else:
            await ctx.respond("你沒有管理者權限用來執行這個指令")

    #將語音頻道內所有人移動到另一個語音頻道
    @commands.slash_command(description="將語音頻道內所有人移動到另一個語音頻道")
    @discord.option("source", type=discord.SlashCommandOptionType.channel, description="源頻道")
    @discord.option("target", type=discord.SlashCommandOptionType.channel, description="目標頻道")
    async def move_voice(self, ctx, source: discord.VoiceChannel, target: discord.VoiceChannel):
        if ctx.author.guild_permissions.administrator:
            # 檢查源頻道是否有人在裡面，如果沒有，則回覆錯誤訊息
            if len(source.members) == 0:
                await ctx.respond(f"[{source.name}] 沒有人在裡面")
                return
            # 創建一個任務列表，用來存放移動成員的任務
            tasks = []
            # 遍歷源頻道的所有成員，將他們移動到目標頻道的任務加入到任務列表中
            for member in source.members:
                tasks.append(member.move_to(target))
            # 使用asyncio.gather函式來同時執行所有的任務，並等待它們完成
            await asyncio.gather(*tasks)
            # 回覆成功訊息
            await ctx.respond(f"已將 [{source.name}] 的所有人移動到 [{target.name}] ") 
        else:
            await ctx.respond("你沒有管理者權限用來執行這個指令") 

    #創建身分組並且添加文字和語音頻道
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