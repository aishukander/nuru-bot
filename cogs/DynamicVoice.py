import discord
from discord.ext import commands
from core.classes import Cog_Extension
import modules.json
from modules.json import DynamicVoice_ID_json_path, DynamicVoice_Name_json_path

voice_channel_set = set()

class DynamicVoice(Cog_Extension):

    origin_channels = {}

    origin_channels = modules.json.open_json(DynamicVoice_ID_json_path)

    @commands.Cog.listener() 
    async def on_voice_state_update(self, member, before, after):

        global voice_channel_set

        guild_id = str(member.guild.id)

        origin_channels = self.origin_channels.get(guild_id)
        if not origin_channels:
            return

        for channel_id in origin_channels:
        
            if after.channel and after.channel.id == channel_id:
                try:
                    DynamicVoiceName = modules.json.open_json(DynamicVoice_Name_json_path)
                    new_channel = await after.channel.clone(name=DynamicVoiceName[f"{guild_id}_VoiceName"].format(member.display_name))
                except:
                    new_channel = await after.channel.clone(name=f"{member.display_name}的動態語音")
            
                await member.move_to(new_channel)
            
                voice_channel_set.add(new_channel.id)
            
            elif before.channel and before.channel.id in voice_channel_set:
          
                if len(before.channel.members) == 0: 
                    await before.channel.delete(reason="Delete empty voice channel")
                    voice_channel_set.remove(before.channel.id)

    @commands.command()
    async def dv(self, ctx, action, name=None):
        global origin_channels
        global DynamicVoice_json_path
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

            for idx, ch_id in enumerate(channels):
            
                channel = self.bot.get_channel(ch_id)
                if channel.name == name:
                
                    await channel.delete()
                
                    del self.origin_channels[guild_id][idx]  
                    if not self.origin_channels[guild_id]:
                        self.origin_channels.pop(guild_id)

                    modules.json.save_DynamicVoice_ID_json(self.origin_channels)

                    try:
                        DynamicVoiceName = modules.json.open_json(DynamicVoice_Name_json_path)

                        del DynamicVoiceName[f"{guild_id}_VoiceName"]

                        modules.json.dump_json(DynamicVoice_Name_json_path, DynamicVoiceName)
                        
                        await ctx.send(f"動態語音 {name} 已刪除")
                    except:
                        await ctx.send("動態語音已刪除")

                    return

            await ctx.send(f"未找到 {name} 動態語音")

    @commands.command()
    async def uvn(self, ctx, new_voice_name):
        # 讀取 DynamicVoiceName.json 文件
        DynamicVoiceName = modules.json.open_json(DynamicVoice_Name_json_path)

        # 更新 VoiceName 的值
        DynamicVoiceName[f'{ctx.guild.id}_VoiceName'] = new_voice_name

        # 將更新後的設定寫回 DynamicVoiceName.json 文件
        modules.json.dump_json(DynamicVoice_Name_json_path, DynamicVoiceName)

        await ctx.send(f'已將動態語音名稱更新為 {new_voice_name}')

async def setup(bot):
    await bot.add_cog(DynamicVoice(bot))