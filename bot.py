import discord
from discord.ext import commands
import json
import random
import os

with open('setting.json','r',encoding='utf8') as jfile:
   jdata = json.load(jfile)

bot = commands.Bot(command_prefix='~')

@bot.event
async def on_ready():
    print(">>Bot is online<<")

@bot.command()
async def ping(ctx):
    await ctx.send(f'{round(bot.latency*1000)}(ms)')

@bot.command()
async def 伊蕾娜(ctx):
   random_pic = random.choice(jdata['pic'])
   await ctx.send(random_pic) 
   await ctx.send('給你香香的伊蕾娜')

@bot.command()
async def load(ctx,extension):
   bot.load_extension(F'cmds.{extension}')
   await ctx.send(F'Loaded {extension} done.')

@bot.command()
async def unload(ctx,extension):
   bot.unload_extension(F'cmds.{extension}')
   await ctx.send(F'Un-Loaded {extension} done.') 

@bot.command()
async def reload(ctx,extension):
   bot.reload_extension(F'cmds.{extension}')
   await ctx.send(F'Re-Loaded {extension} done.')    

@bot.command()
async def em(ctx):
    embed=discord.Embed(title="指令說明", color=0x007bff)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/998902979761549402/999199047200026744/illust_83110343_20220705_172215.jpg")
    embed.add_field(name="~ping", value="給你機器人的ping值", inline=False)
    embed.add_field(name="~伊蕾娜", value="給你香香的伊蕾娜", inline=False)
    embed.add_field(name="~load 所選模塊", value="加載所選的指令模塊", inline=False)
    embed.add_field(name="~unload 所選模塊", value="卸載所選的指令模塊", inline=False)
    embed.add_field(name="~reload 所選模塊", value="重讀所選的指令模塊", inline=False)
    embed.add_field(name="----------------------------------------------------------", value="以下為關鍵字觸發", inline=False)
    embed.add_field(name="字尾包含 好了ㄝ", value="怎麼又好了ㄝ ?", inline=False)
    await ctx.send(embed=embed)

for Filename in os.listdir('./cmds'):
   if Filename.endswith('.py'):
      bot.load_extension(F'cmds.{Filename[:-3]}')


if __name__ == "__main__":

    bot.run(jdata['TOKEN'])