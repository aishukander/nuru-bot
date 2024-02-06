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
    DynamicVoice_json_path = os.path.join(root_dir, "json", "DynamicVoice.json")

    with open(DynamicVoice_json_path,"r",encoding="utf8") as f:
        origin_channels = json.load(f)

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

            self.save_data()
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

                    self.save_data()
                
                    await ctx.send(f"動態語音 {name} 已刪除")
                    return

            await ctx.send(f"未找到 {name} 動態語音")
        
    def save_data(self):
        global origin_channels
        if not self.origin_channels:
            json_str = "{}" 
        else:
            data = {}
            formatted_data = ""
            for guild_id, channel_ids in self.origin_channels.items():
                formatted_data += f'\n"{guild_id}": {channel_ids},'

            json_str = "{" + formatted_data[:-1] + "\n}"

        with open(self.DynamicVoice_json_path,"w",encoding="utf8") as f:
            f.write(json_str)

    @commands.Cog.listener() 
    async def on_voice_state_update(self, member, before, after):

        global voice_channel_set

        guild_id = str(member.guild.id)

        origin_channels = self.origin_channels.get(guild_id)
        if not origin_channels:
            return

        for channel_id in origin_channels:
        
            if after.channel and after.channel.id == channel_id:
            
                new_channel = await after.channel.clone(name=f"{member.display_name}{VoiceName}")
            
                await member.move_to(new_channel)
            
                voice_channel_set.add(new_channel.id)
            
            elif before.channel and before.channel.id in voice_channel_set:
          
                if len(before.channel.members) == 0: 
                    await before.channel.delete(reason="Delete empty voice channel")
                    voice_channel_set.remove(before.channel.id)

async def setup(bot):
    await bot.add_cog(DynamicVoice(bot))