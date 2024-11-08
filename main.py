#各種使用的模組
"""======================================================================================="""
import discord
import os
import random
import modules.json
from modules.json import setting_json_path, token_json_path
"""======================================================================================="""

intents = discord.Intents.all()

#加載setting.json的內容
jdata = modules.json.open_json(setting_json_path)

#加載TOKEN
TOKEN = modules.json.open_json(token_json_path)

bot = discord.Bot()

def CogsList(Loaded = False):
    if Loaded == False:
        CogsList = []
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                CogsList.append(filename[:-3])
        return CogsList
    else:
        Cogslist = []
        for cog in [cog for cog in bot.cogs]:
            Cogslist.append(cog)
        return Cogslist

#載入所有位於cogs的cog
def load_cogs():
    for filename in CogsList(False):
        bot.load_extension(f'cogs.{filename}')
        print(f"載入 {filename} 完成")

load_cogs()

@bot.event
async def on_ready():

    #啟動時會在終端機印出的訊息
    bot_name = f"Bot Logged in as {bot.user}"
    border = "=" * 40
    print(border)
    print(f"= {bot_name.center(len(border) - 4)} =")
    print(f"= {'>>  Bot start  <<'.center(len(border) - 4)} =")
    print(border)

    #bot的狀態顯示
    await bot.change_presence(activity=discord.Game(name="/help general 來獲取指令列表"))

#用於加載、卸載、重讀不同cosg檔
"""======================================================================================="""
cogs = discord.SlashCommandGroup("cogs", "cogs management instructions")

@cogs.command(description="加載指定的cog")
@discord.option("extension", type=discord.SlashCommandOptionType.string, description="cogs名稱", choices = CogsList(False))
async def load(ctx, extension: str):
    #檢測使用者的伺服器管理員權限
    if ctx.author.guild_permissions.administrator:
        try:
            bot.load_extension(f"cogs.{extension}")
            await ctx.respond(f"{extension}模塊加載完成")
        except Exception as e:
            await ctx.respond(f"加載模塊時發生錯誤: {e}")
    #告知使用者沒有管理員權限
    else:
        await ctx.respond("你沒有管理者權限用來執行這個指令")

@cogs.command(description="卸載指定的cog")
@discord.option("extension", type=discord.SlashCommandOptionType.string, description="cogs名稱", choices = CogsList(True))
async def unload(ctx, extension: str):
    if ctx.author.guild_permissions.administrator:
        try:
            bot.unload_extension(f"cogs.{extension}")
            await ctx.respond(f"{extension}模塊卸載完成")
        except Exception as e:
            await ctx.respond(f"卸載模塊時發生錯誤: {e}")
    else:
        await ctx.respond("你沒有管理者權限用來執行這個指令")

@cogs.command(description="重載指定的cog")
@discord.option("extension", type=discord.SlashCommandOptionType.string, description="cogs名稱", choices = CogsList(True))
async def reload(ctx, extension: str):
    if ctx.author.guild_permissions.administrator:
        try:
            bot.reload_extension(f"cogs.{extension}")
            await ctx.respond(f"{extension}模塊重載完成")
        except Exception as e:
            await ctx.respond(f"重載模塊時發生錯誤: {e}")
    else:
        await ctx.respond("你沒有管理者權限用來執行這個指令")

@cogs.command(description="列出已載入的cog")
async def list(ctx):
    if ctx.author.guild_permissions.administrator:
        loaded_cogs = CogsList(True)
        message = "已載入的 cog 如下：\n"
        for cog in loaded_cogs:
            message += f"* {cog}\n"
        await ctx.respond(message)
    else:
        await ctx.respond("你沒有管理者權限用來執行這個指令")

bot.add_application_command(cogs)
"""======================================================================================="""

#測試bot的ping值
@bot.command(description="測試bot的延遲")
async def ping(ctx):
    await ctx.respond(f"{round(bot.latency*1000)}(ms)")

#用來取得bot的邀請連結
@bot.command(description="取得邀請連結")
async def invitation(ctx):
    color = random.randint(0, 16777215)
    embed=discord.Embed(title="------連結------", url=jdata["invitation"], description="狠狠的點下去吧", color=color)
    await ctx.respond(embed=embed)

if __name__ == "__main__":
    bot.run(TOKEN["BOT_TOKEN"])
