from secrets import choice
import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json

with open('setting.json','r',encoding='utf8') as jfile:
   jdata = json.load(jfile)

class React(Cog_Extension): #用於偵測你講出的話後面是否包含偵測中的字詞
   @commands.Cog.listener()
   async def on_message(selF,msg):
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

      if msg.content.endswith('說謊的味道'):
          說謊的味道 = choice(jdata['說謊的味道'])    
          await msg.channel.send(說謊的味道)

      if msg.content.endswith('我不做人啦'):
          我不做人啦 = choice(jdata['我不做人啦'])    
          await msg.channel.send(我不做人啦)

      if msg.content.endswith('典明粥'):
          典明粥 = choice(jdata['典明粥'])    
          await msg.channel.send(典明粥)

      if msg.content.endswith('阿帕茶'):
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

      if msg.content.endswith('yes'):
          joyes = choice(jdata['joyes'])    
          await msg.channel.send(joyes)

      if msg.content.endswith('no'):
          jono = choice(jdata['jono'])    
          await msg.channel.send(jono) 

      if msg.content.endswith('是我啦'):
          dioda = choice(jdata['dioda'])    
          await msg.channel.send(dioda)

      if msg.content.endswith('high到不行'):
          high到不行 = choice(jdata['high到不行'])    
          await msg.channel.send(high到不行)

      if msg.content.endswith('替身攻擊'):
          替身攻擊 = choice(jdata['替身攻擊'])    
          await msg.channel.send(替身攻擊) 

      if msg.content.endswith('想想辦法啊'):
          想想辦法啊 = choice(jdata['想想辦法啊'])    
          await msg.channel.send(想想辦法啊) 

      if msg.content.endswith('西薩'):
          西薩 = choice(jdata['西薩'])    
          await msg.channel.send(西薩) 

      if msg.content.endswith('壓路機'):
          壓路機 = choice(jdata['壓路機'])    
          await msg.channel.send(壓路機)           

      if msg.content.endswith('wryyy'):
          wryyy = choice(jdata['wryyy'])    
          await msg.channel.send(wryyy) 

      if msg.content.endswith('櫻桃'):
          櫻桃 = choice(jdata['櫻桃'])    
          await msg.channel.send(櫻桃) 

      if msg.content.endswith('最後的波紋'):
          最後的波紋 = choice(jdata['最後的波紋'])    
          await msg.channel.send(最後的波紋) 

      if msg.content.endswith('我拒絕'):
          我拒絕 = choice(jdata['我拒絕'])    
          await msg.channel.send(我拒絕) 

      if msg.content.endswith('呦喜'):
          呦喜 = choice(jdata['呦喜'])    
          await msg.channel.send(呦喜) 

      if msg.content.endswith('你下一句話要說的是'):
          你下一句話要說的是 = choice(jdata['你下一句話要說的是'])    
          await msg.channel.send(你下一句話要說的是) 

      if msg.content.endswith('德意志科技世界第一'):
          德意志科技世界第一 = choice(jdata['德意志科技世界第一'])    
          await msg.channel.send(德意志科技世界第一) 

      if msg.content.endswith('玩腿'):
          玩腿 = choice(jdata['玩腿'])    
          await msg.channel.send(玩腿) 

      if msg.content.endswith('nice'):
          nice = choice(jdata['nice'])    
          await msg.channel.send(nice) 

      if msg.content.endswith('成為超棒的單親媽媽的'):
          單親媽 = choice(jdata['單親媽'])    
          await msg.channel.send(單親媽)

      if msg.content.endswith('很戲劇化的發展嗎'):
          戲劇化 = choice(jdata['戲劇化'])    
          await msg.channel.send(戲劇化)    

      if msg.content.endswith('感情問題'):
          感情問題 = choice(jdata['感情問題'])    
          await msg.channel.send(感情問題)                                      

async def setup(bot):
    await bot.add_cog(React(bot))     