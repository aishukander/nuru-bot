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

      if msg.content.endswith('說謊'):
          說謊的味道 = choice(jdata['說謊的味道'])    
          await msg.channel.send(說謊的味道)

      if msg.content.endswith('我不做人啦'):
          我不做人啦 = choice(jdata['我不做人啦'])    
          await msg.channel.send(我不做人啦)

      if msg.content.endswith('粥'):
          典明粥 = choice(jdata['典明粥'])    
          await msg.channel.send(典明粥)

      if msg.content.endswith('茶'):
          阿帕茶 = choice(jdata['阿帕茶'])    
          await msg.channel.send(阿帕茶)

      if msg.content.endswith('喝'):
          喝 = choice(jdata['喝'])    
          await msg.channel.send(喝)

      if msg.content.endswith('勃起'):
          boki = choice(jdata['boki'])    
          await msg.channel.send(boki)

      if msg.content.endswith('救護車'):
          jo護車 = choice(jdata['jo護車'])    
          await msg.channel.send(jo護車)

      if msg.content.endswith('塞車'):
          塞車 = choice(jdata['塞車'])    
          await msg.channel.send(塞車)

      if msg.content.endswith('沒用'):
          沒用 = choice(jdata['沒用'])    
          await msg.channel.send(沒用)

def setup(bot):
  bot.add_cog(React(bot))     