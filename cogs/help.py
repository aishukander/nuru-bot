import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json

with open('setting.json', 'r', encoding='utf8') as jfile:
	 jdata = json.load(jfile)

class help(Cog_Extension):
  #Help指令
  @commands.command()
  async def help(self,ctx):
    embed=discord.Embed(title="Help", color=0x007bff)
    embed.add_field(name="~help", value="指令說明", inline=False)
    embed.add_field(name="~RTsay", value="React列表1", inline=False)
    embed.add_field(name="~RTsay2", value="React列表2", inline=False)
    embed.add_field(name="~invitation", value="給你機器人的邀請連結", inline=False)
    embed.add_field(name="~伊蕾娜", value="給你可愛的伊蕾娜", inline=False)
    embed.add_field(name="@mumei 買不買?", value="讓mumei告訴你該不該買", inline=False)
    embed.add_field(name="~play [連結]", value="撥放指定歌曲", inline=False)
    embed.add_field(name="~pause", value="暫停當前播放的歌曲", inline=False)
    embed.add_field(name="~resume", value="恢復當前暫停的歌曲", inline=False)
    embed.add_field(name="~volume [音量]", value="調整歌曲的音量", inline=False)
    embed.add_field(name="~now", value="顯示當前正在播放的歌曲", inline=False)
    embed.add_field(name="~skip", value="跳過當前這首歌曲", inline=False)
    embed.add_field(name="~queue [頁數]", value="顯示播放對列,您可以選擇指定要顯示的頁面，每頁包含 10 首", inline=False)
    embed.add_field(name="~remove", value="刪除列隊中指定的歌曲", inline=False)
    embed.add_field(name="~loop", value="循環播放當前歌曲，再用一次指令以取消", inline=False)
    embed.add_field(name="~join", value="加入使用者所在的頻道", inline=False)
    await ctx.send(embed=embed)
    
async def setup(bot):
    await bot.add_cog(help(bot))    