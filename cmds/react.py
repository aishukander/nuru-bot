from secrets import choice
import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json

with open('setting.json','r',encoding='utf8') as jfile:
   jdata = json.load(jfile)

class React(Cog_Extension):
   @commands.Cog.listener()
   async def on_message(selF,msg):
      if msg.content.endswith('好了ㄝ'):
          await msg.channel.send('怎麼又好了ㄝ ?') 

      if msg.content.endswith('好甲喔'):
          gay = choice(jdata['gay'])    
          await msg.channel.send(gay) 

      if msg.content.endswith('初吻'):
          dioda = choice(jdata['dioda'])    
          await msg.channel.send(dioda)

      if msg.content.endswith('共匪'):
          共匪 = choice(jdata['共匪'])    
          await msg.channel.send(共匪)

      if msg.content.endswith('龍舌蘭酒'):
          龍舌蘭酒 = choice(jdata['龍舌蘭酒'])    
          await msg.channel.send(龍舌蘭酒)

def setup(bot):
  bot.add_cog(React(bot))     