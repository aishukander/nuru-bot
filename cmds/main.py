import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json

with open('setting.json', 'r', encoding='utf8') as jfile:
	jdata = json.load(jfile)

class Main(Cog_Extension):
  
  @commands.command()
  async def em(self,ctx):
    embed=discord.Embed(title="指令說明", color=0x007bff)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/998902979761549402/999199047200026744/illust_83110343_20220705_172215.jpg")
    embed.add_field(name="~ping", value="給你機器人的ping值", inline=False)
    embed.add_field(name="~伊蕾娜", value="給你香香的伊蕾娜", inline=False)
    embed.add_field(name="~load 所選模塊", value="加載所選的指令模塊", inline=False)
    embed.add_field(name="~unload 所選模塊", value="卸載所選的指令模塊", inline=False)
    embed.add_field(name="~reload 所選模塊", value="重讀所選的指令模塊", inline=False)
    embed.add_field(name="----------------------------------------------------------", value="以下為關鍵字觸發", inline=False)
    embed.add_field(name="字尾包含 好了ㄝ", value="怎麼又好了ㄝ ?", inline=False)
    embed.add_field(name="字尾包含 好甲喔", value="這個地方變得越來越甲了的圖片", inline=False)
    embed.add_field(name="字尾包含 初吻", value="このDIOだ的圖片", inline=False)
    embed.add_field(name="字尾包含 共匪", value="該死的共匪的圖片", inline=False)
    await ctx.send(embed=embed)   

def setup(bot):
  bot.add_cog(Main(bot))