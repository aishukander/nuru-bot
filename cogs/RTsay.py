import discord
from discord.ext import commands
from core.classes import Cog_Extension

class RTsay(Cog_Extension):

    @commands.command()
    async def RTsay(self,ctx):
      embed=discord.Embed(title="React說明1", color=0x007bff)
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
      await ctx.send(embed=embed)

      embed=discord.Embed(title="React說明2", color=0x007bff)
      embed.add_field(name="字尾包含 德意志科技世界第一", value="德意志科技 的圖片", inline=True)
      embed.add_field(name="字尾包含 玩腿", value="玩腿 的圖片", inline=True)
      embed.add_field(name="字尾包含 nice", value="nice 的圖片", inline=True)
      embed.add_field(name="字尾包含 你下一句話要說的是", value="你下一句話 的圖片", inline=True)
      embed.add_field(name="字尾包含 呦喜", value="呦喜呦喜 的圖片", inline=True)
      embed.add_field(name="字尾包含 成為超棒的單親媽媽的", value="成為單親媽媽 的圖片", inline=True)
      embed.add_field(name="字尾包含 很戲劇化的發展嗎", value="戲劇化發展 的圖片", inline=True)
      embed.add_field(name="字尾包含 感情問題", value="感情的問題一律分手 的圖片", inline=True)
      embed.add_field(name="tag 我的話", value="會需要等我跑過來", inline=True)
      embed.add_field(name="tag bot問他買不買?", value="他會告訴你要不要買(記得句尾要有問號)", inline=True)
      embed.add_field(name="字尾包含 令人驚豔", value="令人晶彥章魚哥 的圖片", inline=True)
      await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RTsay(bot))