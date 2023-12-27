#各種使用的模組
'''======================================================================================='''
import discord
from discord.ext import commands
import os
import json
import random
import asyncio
'''======================================================================================='''

intents = discord.Intents.all()

#加載setting.json的內容
with open('setting.json','r',encoding='utf8') as jfile:
    jdata = json.load(jfile)

#加載TOKEN
with open('token.json','r',encoding='utf8') as tfile:
    TOKEN = json.load(tfile)

#呼喚bot的前綴
bot = commands.Bot(command_prefix='~',intents=intents)

#刪除help指令
bot.remove_command('help')

@bot.event
async def on_ready():
    #載入所有位於cogs的cog
    cog_path = "cogs"
    extensions = []

    for filepath in os.listdir(cog_path):
        if filepath.endswith('.py') and not filepath.startswith('_'):
            cog = f'{cog_path}.{filepath[:-3]}'
            extensions.append(cog)
    await asyncio.gather(*[bot.load_extension(ext) for ext in extensions])

    #啟動時會在終端機印出的訊息
    print(f"=========================================")
    print(f"=   mumei Bot Logged in as {bot.user}   =")
    print(f"=             >>Bot start<<             =")
    print(f"=========================================")

    #bot的狀態顯示
    await bot.change_presence(activity=discord.Game(name="~help 來獲取指令列表"))

#用於加載、卸載、重讀不同cosg檔
'''======================================================================================='''
@bot.command()
async def load(ctx, extension):
    #檢測使用者的伺服器管理員權限
    if ctx.author.guild_permissions.administrator:
        try:
            await bot.load_extension(f"cogs.{extension}")
            await ctx.send(f"{extension}模塊加載完成")
        except Exception as e:
            await ctx.send(f"加載模塊時發生錯誤: {e}")
    #告知使用者沒有管理員權限
    else:
        await ctx.send("你沒有管理者權限用來執行這個指令")

@bot.command()
async def unload(ctx, extension):
    if ctx.author.guild_permissions.administrator:
        try:
            await bot.unload_extension(f"cogs.{extension}")
            await ctx.send(f"{extension}模塊卸載完成")
        except Exception as e:
            await ctx.send(f"卸載模塊時發生錯誤: {e}")
    else:
        await ctx.send("你沒有管理者權限用來執行這個指令")

@bot.command()
async def reload(ctx, extension):
    if ctx.author.guild_permissions.administrator:
        try:
            await bot.reload_extension(f"cogs.{extension}")
            await ctx.send(f"{extension}模塊重載完成")
        except Exception as e:
            await ctx.send(f"重載模塊時發生錯誤: {e}")
    else:
        await ctx.send("你沒有管理者權限用來執行這個指令")
'''======================================================================================='''

#從二十幾張伊蕾娜的圖片中給你一張
@bot.command()
async def 伊蕾娜(ctx):
    random_pic = random.choice(jdata['Elaina'])
    await ctx.send(random_pic)
    await ctx.send('給你可愛的伊蕾娜')

#用來取得bot的邀請連結
@bot.command()
async def invitation(ctx):
    embed=discord.Embed(title="------連結------", url="https://discord.com/api/oauth2/authorize?client_id=999157840063242330&permissions=318364711936&scope=bot", description="狠狠的點下去吧", color=0x007bff)
    await ctx.send(embed=embed)

#測試bot的ping值
@bot.command()
async def ping(ctx):
    await ctx.send(f'{round(bot.latency*1000)}(ms)')

tag_on = 0
#管理tag回覆功能指令
@bot.command()
async def tag(ctx, action: str):
    if ctx.author.guild_permissions.administrator:
        global tag_on
        if action.lower() == "on":
            tag_on = 1
            await ctx.send("已啟用tag功能")
        
        elif action.lower() == "off":
            tag_on = 0
            await ctx.send("已暫時關閉tag功能")
        
        else:
            await ctx.send("無效的動作參數, 請使用 `on` 或 `off`")
    else:
        await ctx.send("你沒有管理者權限用來執行這個指令")

#tag回覆功能本體
@bot.event
async def on_message(msg):
    if tag_on and "405704403937525782" in msg.content and msg.author != bot.user:
        await msg.channel.send("十秒だけ持ちこたえてくれ!")
    await bot.process_commands(msg)

if __name__ == "__main__":
    bot.run(TOKEN["BOT_TOKEN"])