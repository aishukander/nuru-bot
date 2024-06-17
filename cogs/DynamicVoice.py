import discord
from discord.ext import commands
import modules.json
from modules.json import DynamicVoice_ID_json_path, DynamicVoice_Name_json_path

class DynamicVoice(commands.Cog):

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

    @commands.command()
    async def dv(self, ctx, action, name=None):
        if ctx.author.guild_permissions.administrator:
            guild_id = str(ctx.guild.id)

            if action.lower() == "add":
                channel = await ctx.guild.create_voice_channel(name)
        
                if guild_id not in self.origin_channels:
                    self.origin_channels[guild_id] = []
            
                self.origin_channels[guild_id].append(channel.id)

                modules.json.save_DynamicVoice_ID_json(self.origin_channels)
                await ctx.send(f"動態語音 {channel.name} 已建立")

            elif action.lower() == "remove":
                channels = self.origin_channels.get(guild_id)
                if not channels:
                    return await ctx.send("此伺服器未設定動態語音")

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
                        
                            await ctx.send(f"動態語音 {name} 已刪除")
                        except:
                            await ctx.send("動態語音已刪除")

                        return

                await ctx.send(f"未找到 {name} 動態語音")
        else:
            await ctx.send("你沒有管理者權限用來執行這個指令")

    @commands.command()
    async def uvn(self, ctx,parent_channel_name, new_voice_name):
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
                await ctx.send(f'未找到名為 {parent_channel_name} 的母頻道')
                return

            # 更新 VoiceName 的值
            DynamicVoiceName[f'{ctx.guild.id}_{parent_channel.id}'] = new_voice_name

            # 將更新後的設定寫回 DynamicVoiceName.json 文件
            modules.json.dump_json(DynamicVoice_Name_json_path, DynamicVoiceName, 4)

            await ctx.send(f'已將 {parent_channel_name} 的子頻道名稱更新為 {new_voice_name}')
        else:
            await ctx.send("你沒有管理者權限用來執行這個指令")

def setup(bot):
    bot.add_cog(DynamicVoice(bot))