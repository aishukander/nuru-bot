import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json
import os

VoiceName = "的動態語音" #名稱格式為[進入動態語音之使用者名][VoiceName的字串]
voice_channel_set = set()

class DynamicVoice(Cog_Extension):

    origin_channels = {}
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DynamicVoice_json_path = os.path.join(root_dir, "json\\DynamicVoice.json")

    with open(DynamicVoice_json_path,"r",encoding="utf8") as f:
        origin_channels = json.load(f)

    # 定義 dv 指令用於創建母頻道
    @commands.command()
    async def dv(self, ctx, action: str, name: str):
        if ctx.author.guild_permissions.administrator:
            if action.lower() == "add":
                global origin_channels
                global DynamicVoice_json_path
                origin_channel = await ctx.guild.create_voice_channel(name=name) 
                self.origin_channels[str(ctx.guild.id)] = origin_channel.id
                await ctx.send(f"動態語音 {origin_channel.name} 已建立")

                # 將更新後的動態資料寫入 JSON 文件
                with open(self.DynamicVoice_json_path,"w",encoding="utf8") as f:
                    json.dump(self.origin_channels, f, indent=2)

            elif action.lower() == "remove" and name.lower() == "true":
                guild_id = str(ctx.guild.id) 
                if guild_id in self.origin_channels:
                    origin_channel_id = self.origin_channels[guild_id]
                    origin_channel = self.bot.get_channel(origin_channel_id)
                    await origin_channel.delete()
        
                    with open(self.DynamicVoice_json_path,"r",encoding="utf8") as f:
                        json_data = json.load(f)
                        json_data.pop(guild_id)
            
                    with open(self.DynamicVoice_json_path,"w",encoding="utf8") as f:  
                        json.dump(json_data, f, indent=2)
            
                    await ctx.send("動態語音已刪除") 
                else:
                    await ctx.send("此伺服器未設定動態語音")

    # 監聽語音頻道變化事件
    @commands.Cog.listener() 
    async def on_voice_state_update(self, member, before, after):
        global voice_channel_set
        global VoiceName
        guild_id = member.guild.id
        # 從 JSON 文件中獲取當前服務器的母頻道 ID
        origin_channel_id = self.origin_channels.get(str(guild_id))
        # 如果成員加入了一個語音頻道
        if after.channel and after.channel.id == origin_channel_id:
                # 創建一個新的語音頻道，名稱為成員的暱稱，類型為語音，位於原始頻道的下方
                new_voice_channel = await after.channel.clone(name=f"{member.display_name}{VoiceName}", reason="Create new voice channel")
                # 將成員移動到新的語音頻道
                await member.move_to(new_voice_channel, reason="Move to new voice channel")
                # 將新的語音頻道的ID加入到集合中，以便之後使用
                voice_channel_set.add(new_voice_channel.id)
        
        # 如果成員離開了一個語音頻道
        if before.channel and before.channel.id in voice_channel_set:
                # 如果該語音頻道沒有任何成員了，也就是空的
                if len(before.channel.members) == 0:
                    # 刪除該語音頻道，並從集合中移除它的ID
                    await before.channel.delete(reason="Delete empty voice channel")
                    voice_channel_set.remove(before.channel.id)

async def setup(bot):
    await bot.add_cog(DynamicVoice(bot))