'''=======================================================================================''' #這個框內的是各種使用的模組
import discord
from discord.ext import commands
import json
import random
from secrets import choice
'''======================================================================================='''
from cogs.help import Help #這裡from開頭的是引入cogs內的模組 在cosg.後面的是位於cosg資料夾內的檔名，import後面的是檔案內設定的名稱
from cogs.react import React

intents = discord.Intents.all()

with open('setting.json','r',encoding='utf8') as jfile: #引用setting.json的內容
   jdata = json.load(jfile)

bot = commands.Bot(command_prefix='~',intents=intents) #''內的是呼喚bot的前綴

bot.remove_command('help') #刪除help指令

@bot.event
async def on_ready():
    await bot.load_extension("cogs.help") #""內是載入對應的cogs檔
    await bot.load_extension("cogs.react")

    print(f"目前登入身份 --> {bot.user}")  #這兩行是啟動時會在終端機印出的訊息
    print(">>Bot start<<")                #^

'''======================================================================================='''#這個框內的是用於加載、卸載、重讀不同cosg檔
@bot.command()
async def load(ctx, extension):
    await bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"{extension} 加載完成")

@bot.command()
async def unload(ctx, extension):
    await bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"{extension} 卸載完成")

@bot.command()
async def reload(ctx, extension):
    await bot.reload_extension(f"cogs.{extension}")
    await ctx.send(f"{extension} 重載完成")
'''======================================================================================='''

@bot.command() #從二十幾張伊蕾娜的圖片中給你一張
async def 伊蕾娜(ctx):
   random_pic = random.choice(jdata['Elaina'])
   await ctx.send(random_pic) 
   await ctx.send('給你香香的伊蕾娜')   

@bot.command() #用來取得bot的邀請連結
async def join(ctx):
   embed=discord.Embed(title="------連結------", url="https://discord.com/api/oauth2/authorize?client_id=999157840063242330&permissions=318364711936&scope=bot", description="狠狠的點下去吧", color=0x007bff)
   await ctx.send(embed=embed)   

@bot.command() #測試bot的ping值
async def ping(ctx):
    await ctx.send(f'{round(bot.latency*1000)}(ms)')

@bot.event #tag我時bot會講出 等我從現在的情況逃げるんだよォ過來一下
async def on_message(msg):
    if "405704403937525782" in msg.content and msg.author != bot.user:
          await msg.channel.send('等我從現在的情況逃げるんだよォ過來一下') 
    await bot.process_commands(msg)   

if __name__ == "__main__":

    bot.run(jdata['TOKEN'])