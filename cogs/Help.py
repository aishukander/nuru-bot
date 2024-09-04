import discord
from discord.ext import commands
import random

class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    help = discord.SlashCommandGroup("help", "help command group")

    #help指令
    @help.command(description="一般使用者的指令說明")
    async def general(self,ctx):
        color = random.randint(0, 16777215)
        embed=discord.Embed(title="help", color=color)
        embed.add_field(name="@mumei [任意訊息]", value="讓mumei回答你(可以使用圖片)", inline=False)
        embed.add_field(name="@mumei RESET", value="清除使用者的訊息歷史記錄", inline=False)
        embed.add_field(name="/bot_info", value="獲取機器人的資訊", inline=False)
        embed.add_field(name="/buy_or_not", value="讓mumei告訴你該不該買", inline=False)
        embed.add_field(name="/help admin", value="管理員指令說明(需管理者權限)", inline=False)
        embed.add_field(name="/help general", value="指令說明", inline=False)
        embed.add_field(name="/invitation", value="給你機器人的邀請連結", inline=False)
        embed.add_field(name="/mc_status [伺服器地址] [port(未輸入時預設25565)]", value="查看指定Minecraft伺服器的狀態", inline=False)
        embed.add_field(name="/notebook", value="讓bot私訊你來呈現一個記事本", inline=False)
        embed.add_field(name="/ping", value="PingBot", inline=False)
        embed.add_field(name="/word_changer [欲修改文本] [欲修改的字] [修改為的字]", value="用來批量替換文本內的單字", inline=False)
        await ctx.respond(embed=embed)

    #AdminHelp指令
    @help.command(description="管理員的指令說明")
    async def admin(self,ctx):
        if ctx.author.guild_permissions.administrator:
            color = random.randint(0, 16777215)
            embed=discord.Embed(title="AdminHelp", color=color)
            embed.add_field(name="@mumei [任意訊息]", value="讓mumei回答你(可以使用圖片)", inline=False)
            embed.add_field(name="@mumei RESET", value="清除使用者的訊息歷史記錄", inline=False)
            embed.add_field(name="/buy_or_not", value="讓mumei告訴你該不該買", inline=False)
            embed.add_field(name="/cogs list", value="顯示已載入的指令模塊", inline=False)
            embed.add_field(name="/cogs load [所選模塊]", value="加載所選的指令模塊(需管理者權限)", inline=False)
            embed.add_field(name="/cogs reload [所選模塊]", value="重載所選的指令模塊(需管理者權限)", inline=False)
            embed.add_field(name="/cogs unload [所選模塊]", value="卸載所選的指令模塊(需管理者權限)", inline=False)
            embed.add_field(name="/create_role [身分組]", value="添加對應身分組與其的專用頻道(需管理者權限)", inline=False)
            embed.add_field(name="/delete_msg [訊息數]", value="在此頻道刪除所選數量的訊息(需管理者權限)", inline=False)
            embed.add_field(name="/dynamic_voice management [add/remove] [動態語音名]", value="管理動態語音(需管理者權限)", inline=False)
            embed.add_field(name="/dynamic_voice update_voice_name [要修改的母頻道名] [要修改為的動態語音名]", value="範例:~uvn {}的動態語音({}代表第一個進入語音的使用者)(需管理者權限)", inline=False)
            embed.add_field(name="/gemini_private_management [on或off]", value="管理Gemini在私訊時是否直接回覆(需管理者權限)", inline=False)
            embed.add_field(name="/help admin", value="管理員指令說明(需管理者權限)", inline=False)
            embed.add_field(name="/help general", value="指令說明", inline=False)
            embed.add_field(name="/info_bot", value="獲取機器人的資訊", inline=False)
            embed.add_field(name="/invitation", value="給你機器人的邀請連結", inline=False)
            embed.add_field(name="/mc_status [伺服器地址] [port(未輸入時預設25565)]", value="查看指定Minecraft伺服器的狀態", inline=False)
            embed.add_field(name="/move_voice [目前頻道ID] [目標頻道ID]", value="將語音頻道內所有人移動到另一個語音頻道 (需管理者權限)", inline=False)
            embed.add_field(name="/notebook", value="讓bot私訊你來呈現一個記事本", inline=False)
            embed.add_field(name="/ping", value="PingBot", inline=False)
            embed.add_field(name="/say [要覆誦的話]", value="刪除所傳的訊息並覆誦(需管理者權限)", inline=False)
            embed.add_field(name="/send_msg [要傳送的訊息] [伺服器] [頻道名]", value="傳送訊息至指定位置(需管理者權限)", inline=False)
            embed.add_field(name="/word_changer [欲修改文本] [欲修改的字] [修改為的字]", value="用來批量替換文本內的單字", inline=False)
            #
            await ctx.respond(embed=embed)

            #embed=discord.Embed(title="AdminHelp", color=color)

            #await ctx.send(embed=embed)   
        else:
            await ctx.respond("你沒有管理者權限用來執行這個指令")
    
def setup(bot):
    bot.add_cog(Help(bot))    
