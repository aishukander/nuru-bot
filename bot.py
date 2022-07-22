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
async def join(ctx):
   embed=discord.Embed(title="------連結------", url="https://discord.com/api/oauth2/authorize?client_id=999157840063242330&permissions=318364711936&scope=bot", description="狠狠的點下去吧", color=0x007bff)
   await ctx.send(embed=embed)   


for Filename in os.listdir('./cmds'):
   if Filename.endswith('.py'):
      bot.load_extension(F'cmds.{Filename[:-3]}')


if __name__ == "__main__":

    bot.run(jdata['TOKEN']