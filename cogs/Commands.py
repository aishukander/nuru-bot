import discord
from discord.ext import commands
from core.classes import Cog_Extension
import re
import asyncio
from secrets import choice
import json
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
setting_json_path = os.path.join(root_dir, "json\\Setting.json")

with open(setting_json_path,"r",encoding="utf8") as jfile:
   jdata = json.load(jfile)

class Commands(Cog_Extension):

    #刪除所傳的訊息並讓機器人覆誦
    @commands.command()
    async def say(self,ctx,msg):
        if ctx.author.guild_permissions.administrator:
            await ctx.message.delete()
            await ctx.send(msg)
        else:
            await ctx.send("你沒有管理者權限用來執行這個指令")

    #刪除所選數量的訊息
    @commands.command()
    async def delete(self,ctx,num:int):
        if ctx.author.guild_permissions.administrator:
            #刪除訊息(因為指令也算一條訊息 所以num+1)
            await ctx.channel.purge(limit=num+1)
        else:
            await ctx.send("你沒有管理者權限用來執行這個指令")

    #ban除選定人物
    @commands.command()
    async def ban(self, ctx, member: discord.Member):
        if ctx.author.guild_permissions.administrator:
            await member.ban()
            await ctx.send(f'{member} 已踢出伺服器')
        else:
            await ctx.send("你沒有管理者權限用來執行這個指令")

    #Word-Changer功能的整合
    @commands.command()
    async def reword(self,ctx,msg):
        text = msg
        await ctx.send("請輸入要替換的單字：")
        #定義檢查函數來確保只接受用戶自己在同一頻道的訊息
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel
        try:
            #等待用戶輸入並將訊息存入old參數裡，並且超過6秒沒有回覆就引發異常
            old = await self.bot.wait_for('message', check=check, timeout=6)
            await ctx.send("請輸入要替換成的單字：")
            #等待用戶輸入並將訊息存入new參數裡，並且超過6秒沒有回覆就引發異常
            new = await self.bot.wait_for('message', check=check, timeout=6)
            #將old與new參數傳遞給re.sub函數並完成文本修改
            new_text = re.sub(old.content, new.content, text)
            await ctx.send(new_text)
        except asyncio.TimeoutError:
            #如果發生超時異常，則取消指令並通知用戶
            await ctx.send("您沒有及時回覆，指令已取消。")

    #讓bot私訊你來呈現一個小型資訊放置處
    @commands.command()
    async def drive(self, ctx):
        user = ctx.author
        embed=discord.Embed(title="It's a cloud drive.", color=0x007bff)
        await user.send(embed=embed)

    #將語音頻道內所有人移動到另一個語音頻道
    @commands.command()
    async def move(self, ctx, source: discord.VoiceChannel, target: discord.VoiceChannel):
        if ctx.author.guild_permissions.administrator:
            # 檢查源頻道是否有人在裡面，如果沒有，則回覆錯誤訊息
            if len(source.members) == 0:
                await ctx.send(f"[{source.name}] 沒有人在裡面")
                return
            # 創建一個任務列表，用來存放移動成員的任務
            tasks = []
            # 遍歷源頻道的所有成員，將他們移動到目標頻道的任務加入到任務列表中
            for member in source.members:
                tasks.append(member.move_to(target))
            # 使用asyncio.gather函式來同時執行所有的任務，並等待它們完成
            await asyncio.gather(*tasks)
            # 回覆成功訊息
            await ctx.send(f"已將 [{source.name}] 的所有人移動到 [{target.name}] ") 
        else:
            await ctx.send("你沒有管理者權限用來執行這個指令") 

    #創建身分組並且添加文字和語音頻道
    @commands.command()
    async def role(self, ctx, name):
        guild = ctx.guild
        role = await guild.create_role(name=name)
        category = await guild.create_category(name)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            role: discord.PermissionOverwrite(read_messages=True),
        }
        channel1 = await category.create_text_channel(name, overwrites=overwrites)
        channel2 = await category.create_voice_channel(name, overwrites=overwrites)
        await ctx.send("完成")

    @commands.command() 
    async def 買不買(self,msg):
        買不買 = choice(jdata['買不買'])
        await msg.channel.send(買不買)    

    @commands.command()
    async def msg(self, ctx, message, guild_name, channel_name):
        if ctx.author.guild_permissions.administrator:
            guild = discord.utils.find(lambda g: g.name == guild_name, self.bot.guilds)
            if guild is None:
                return await ctx.send("未找到伺服器!")
        
            channel = discord.utils.find(lambda c: c.name == channel_name, guild.text_channels)
            if channel is None: 
                 return await ctx.send("未找到頻道!")
         
            try:
                await channel.send(message)
                await ctx.send(f"訊息已成功發送至 {guild.name} 的 {channel} 頻道!") 
            except:
                await ctx.send("訊息發送錯誤！")
        else:
            await ctx.send("你沒有管理者權限用來執行這個指令") 

async def setup(bot):
    await bot.add_cog(Commands(bot))
