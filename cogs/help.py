import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json

with open('setting.json', 'r', encoding='utf8') as jfile:
	jdata = json.load(jfile)

class Help(Cog_Extension):
  
  @commands.command()
  async def help(self,ctx):
    embed=discord.Embed(title="指令說明-1", color=0x007bff)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/998902979761549402/999199047200026744/illust_83110343_20220705_172215.jpg")
    embed.add_field(name="~help", value="前部分指令", inline=False)
    embed.add_field(name="~help2", value="後部分指令", inline=False)
    embed.add_field(name="~ping", value="給你機器人的ping值", inline=False)
    embed.add_field(name="~join", value="給你機器人的邀請連結", inline=False)
    embed.add_field(name="~伊蕾娜", value="給你香香的伊蕾娜", inline=False)
    embed.add_field(name="~load 所選模塊", value="加載所選的指令模塊", inline=False)
    embed.add_field(name="~unload 所選模塊", value="卸載所選的指令模塊", inline=False)
    embed.add_field(name="~reload 所選模塊", value="重讀所選的指令模塊", inline=False)
    embed.add_field(name="----------------------------------------------------------", value="以下為關鍵字觸發", inline=False)
    embed.add_field(name="字尾包含 好了ㄝ", value="怎麼又好了ㄝ ?", inline=True)
    embed.add_field(name="字尾包含 好甲喔", value="這個地方變得越來越甲了的圖片", inline=True)
    embed.add_field(name="字尾包含 初吻", value="このDIOだ的圖片", inline=True)
    embed.add_field(name="字尾包含 共匪", value="該死的共匪的圖片", inline=True)
    embed.add_field(name="字尾包含 龍舌蘭酒", value="龍舌蘭酒姑娘的圖片", inline=True)
    embed.add_field(name="字尾包含 說謊的味道", value="這是說謊的味道的圖片", inline=True)
    embed.add_field(name="字尾包含 我不做人啦", value="我不做人啦JOJO的圖片", inline=True)
    embed.add_field(name="字尾包含 典明粥", value="典明粥的圖片", inline=True)
    embed.add_field(name="字尾包含 阿帕茶", value="阿帕茶的圖片", inline=True)
    embed.add_field(name="字尾包含 喝", value="喝的圖片", inline=True)
    embed.add_field(name="字尾包含 勃起", value="boki的圖片", inline=True)
    embed.add_field(name="字尾包含 救護車", value="jojo護車的圖片", inline=True)
    embed.add_field(name="字尾包含 沒用", value="沒用的圖片", inline=True)
    embed.add_field(name="字尾包含 塞車", value="行人道很寬敞的圖片", inline=True)
    embed.add_field(name="字尾包含 yes", value="yes yes的圖片", inline=True)
    await ctx.send(embed=embed)   

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

async def setup(bot):
    await bot.add_cog(Help(bot))