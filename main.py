#各種使用的模組
'''======================================================================================='''
import discord
from discord.ext import commands
import json
import random
import os
import asyncio
'''======================================================================================='''

intents = discord.Intents.all()

#引用setting.json的內容
with open('setting.json','r',encoding='utf8') as jfile:
   jdata = json.load(jfile)

#呼喚bot的前綴
bot = commands.Bot(command_prefix='~',intents=intents)

#刪除help指令
bot.remove_command('help')

#載入對應的cogs檔
@bot.event
async def on_ready():
    extensions = ["cogs.RTsay", "cogs.react", "cogs.help", "cogs.music", "cogs.roothelp", "cogs.cmd", "cogs.BON", "cogs.role"]
    await asyncio.gather(*[bot.load_extension(ext) for ext in extensions])

    #啟動時會在終端機印出的訊息
    print(f"目前登入身份 --> {bot.user}")
    print(">>Bot start<<")

#用於加載、卸載、重讀不同cosg檔
'''======================================================================================='''
@bot.command()
async def load(ctx, extension):
    if ctx.author.guild_permissions.administrator:
        await bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"{extension}模塊加載完成")
    else:
        await ctx.send("你沒有管理者權限用來執行這個指令")

@bot.command()
async def unload(ctx, extension):
    if ctx.author.guild_permissions.administrator:
        await bot.unload_extension(f"cogs.{extension}")
        await ctx.send(f"{extension}模塊卸載完成")
    else:
        await ctx.send("你沒有管理者權限用來執行這個指令")

@bot.command()
async def reload(ctx, extension):
    if ctx.author.guild_permissions.administrator:
        await bot.reload_extension(f"cogs.{extension}")
        await ctx.send(f"{extension}模塊重載完成")
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

#tag我時bot會講出 等我從現在的情況逃げるんだよォ過來一下
@bot.event
async def on_message(msg):
    if "405704403937525782" in msg.content and msg.author != bot.user:
          await msg.channel.send('等我從現在的情況逃げるんだよォ過來一下')
    await bot.process_commands(msg)

if __name__ == "__main__":
   bot.run(jdata['TOKEN'])