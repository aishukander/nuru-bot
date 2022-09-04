import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json

with open('setting.json', 'r', encoding='utf8') as jfile:
	jdata = json.load(jfile)

class Maom(Cog_Extension):    

  @commands.command()
  async def help2(self,ctx):
    embed=discord.Embed(title="指令說明-2", color=0x007bff)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/998902979761549402/999199047200026744/illust_83110343_20220705_172215.jpg")
    embed.add_field(name="字尾包含 no", value="no no的圖片", inline=True)
    embed.add_field(name="字尾包含 是我啦", value="このDIOだ的圖片", inline=True)
    embed.add_field(name="字尾包含 high到不行", value="high到不行 的圖片", inline=True)
    embed.add_field(name="字尾包含 替身攻擊", value="替身攻擊 的圖片", inline=True)
    embed.add_field(name="字尾包含 想想辦法啊", value="想想辦法啊 的圖片", inline=True)
    embed.add_field(name="字尾包含 西薩", value="西薩 的圖片", inline=True)
    embed.add_field(name="字尾包含 壓路機", value="壓路機 的圖片", inline=True)
    embed.add_field(name="字尾包含 wryyy", value="wryyy 的圖片", inline=True)
    embed.add_field(name="字尾包含 櫻桃", value="花京院吃櫻桃 的圖片", inline=True)
    embed.add_field(name="字尾包含 最後的波紋", value="最後的波紋 的圖片", inline=True)
    embed.add_field(name="字尾包含 我拒絕", value="我拒絕 的圖片", inline=True)
    embed.add_field(name="字尾包含 德意志科技世界第一", value="德意志科技 的圖片", inline=True)
    embed.add_field(name="字尾包含 玩腿", value="玩腿 的圖片", inline=True)
    embed.add_field(name="字尾包含 nice", value="nice 的圖片", inline=True)
    embed.add_field(name="字尾包含 你下一句話要說的是", value="你下一句話 的圖片", inline=True)
    embed.add_field(name="字尾包含 呦喜", value="呦喜呦喜 的圖片", inline=True)
    embed.add_field(name="字尾包含 成為超棒的單親媽媽的", value="成為單親媽媽 的圖片", inline=True)
    embed.add_field(name="字尾包含 很戲劇化的發展嗎", value="戲劇化發展 的圖片", inline=True)
    embed.add_field(name="字尾包含 感情問題", value="感情的問題一律分手 的圖片", inline=True)
    embed.add_field(name="tag 我的話", value="rick roll你", inline=True)
    await ctx.send(embed=embed)   

def setup(bot):
  bot.add_cog(Maom(bot))    