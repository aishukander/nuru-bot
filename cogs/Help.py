import discord
from discord.ext import commands
import random

class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #help指令
    @commands.command()
    async def help(self,ctx):
        color = random.randint(0, 16777215)
        embed=discord.Embed(title="help", color=color)
        embed.add_field(name="@mumei [任意訊息]", value="讓mumei回答你(可以使用圖片)", inline=False)
        embed.add_field(name="@mumei RESET", value="清除使用者的訊息歷史記錄", inline=False)
        embed.add_field(name="~adminhelp", value="管理員指令說明(需管理者權限)", inline=False)
        embed.add_field(name="~buyornot", value="讓mumei告訴你該不該買", inline=False)
        embed.add_field(name="~drive", value="讓bot私訊你來呈現一個小型資訊放置處", inline=False)
        embed.add_field(name="~help", value="指令說明", inline=False)
        embed.add_field(name="~invitation", value="給你機器人的邀請連結", inline=False)
        embed.add_field(name="~join", value="加入使用者所在的頻道", inline=False)
        embed.add_field(name="~leave", value="清空隊列並且離開語音通道", inline=False)
        embed.add_field(name="~loop", value="循環播放當前歌曲，再用一次指令以取消", inline=False)
        embed.add_field(name="~lottery [tag使用者(每個使用者以空格分開)]", value="開始抽籤(點擊⚙️顯示目前抽籤權重、點擊▶️抽籤)", inline=False)
        embed.add_field(name="~mcstatus [伺服器地址] [port(未輸入時預設25565)]", value="查看指定Minecraft伺服器的狀態", inline=False)
        embed.add_field(name="~now", value="顯示當前正在播放的歌曲", inline=False)
        embed.add_field(name="~pause", value="暫停當前播放的歌曲", inline=False)
        embed.add_field(name="~ping", value="PingBot", inline=False)
        embed.add_field(name="~play [連結]", value="撥放指定歌曲", inline=False)
        embed.add_field(name="~queue [頁數]", value="顯示播放對列,您可以選擇指定要顯示的頁面，每頁包含 10 首", inline=False)
        embed.add_field(name="~remove", value="刪除列隊中指定的歌曲", inline=False)
        embed.add_field(name="~reword [欲修改文本]", value="用來批量替換文本內的單字", inline=False)
        embed.add_field(name="~resume", value="恢復當前暫停的歌曲", inline=False)
        embed.add_field(name="~show", value="顯示偵測中的單字偵測次數", inline=False)
        embed.add_field(name="~skip", value="跳過當前這首歌曲", inline=False)
        embed.add_field(name="~volume [音量]", value="調整歌曲的音量", inline=False)
        embed.add_field(name="~weight [tag使用者] [權重]", value="修改抽籤中籤的權重", inline=False)
        await ctx.send(embed=embed)
    
def setup(bot):
    bot.add_cog(Help(bot))    
