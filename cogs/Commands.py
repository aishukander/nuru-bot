import discord
from discord.ext import commands
import re
import asyncio
import random
from secrets import choice
import modules.json
from modules.json import setting_json_path

class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.jdata = modules.json.open_json(setting_json_path)

    #讓機器人覆誦你輸入的訊息
    @commands.slash_command(description="讓機器人覆誦你輸入的訊息")
    @discord.option("msg", type=discord.SlashCommandOptionType.string, description="要覆誦的訊息")
    async def say(self, ctx, msg: str):
        if ctx.author.guild_permissions.administrator:
            await ctx.respond(msg)
        else:
            await ctx.respond("你沒有管理者權限用來執行這個指令")

    #刪除所選數量的訊息
    @commands.slash_command(description="刪除所選數量的訊息")
    @discord.option("num", type=discord.SlashCommandOptionType.integer, description="要刪除的訊息數量")
    async def delete(self, ctx, num: int):
        if ctx.author.guild_permissions.administrator:
            await ctx.respond(f"準備開始刪除 {num} 則訊息")
            await asyncio.sleep(1)
            await ctx.channel.purge(limit=num+1)
            await ctx.send(f"已刪除 {num} 則訊息")
        else:
            await ctx.respond("你沒有管理者權限用來執行這個指令")

    #ban除選定人物
    @commands.slash_command(description="ban除選定人物")
    @discord.option("member", type=discord.SlashCommandOptionType.user, description="要ban除的人物")
    async def ban(self, ctx, member: discord.Member):
        if ctx.author.guild_permissions.administrator:
            await member.ban()
            await ctx.respond(f'{member} 已踢出伺服器')
        else:
            await ctx.respond("你沒有管理者權限用來執行這個指令")

    #Word-Changer功能的整合
    @commands.slash_command(description="Word-Changer功能的整合")
    @discord.option("text", type=discord.SlashCommandOptionType.string, description="要修改的文字")
    @discord.option("old_msg", type=discord.SlashCommandOptionType.string, description="要被取代的文字")
    @discord.option("new_msg", type=discord.SlashCommandOptionType.string, description="新的文字")
    async def reword(self, ctx, text: str, old_msg: str, new_msg: str):
        new_text = re.sub(old_msg, new_msg, text)
        await ctx.respond(new_text)

    #讓bot私訊你來呈現一個小型資訊放置處
    @commands.slash_command(description="讓bot私訊你來呈現一個小型資訊放置處")
    async def drive(self, ctx):
        color = random.randint(0, 16777215)
        user = ctx.author
        embed=discord.Embed(title="It's a cloud drive.", color=color)
        await user.send(embed=embed)
        await ctx.respond("完成")

    #將語音頻道內所有人移動到另一個語音頻道
    @commands.slash_command(description="將語音頻道內所有人移動到另一個語音頻道")
    @discord.option("source", type=discord.SlashCommandOptionType.channel, description="源頻道")
    @discord.option("target", type=discord.SlashCommandOptionType.channel, description="目標頻道")
    async def move(self, ctx, source: discord.VoiceChannel, target: discord.VoiceChannel):
        if ctx.author.guild_permissions.administrator:
            # 檢查源頻道是否有人在裡面，如果沒有，則回覆錯誤訊息
            if len(source.members) == 0:
                await ctx.respond(f"[{source.name}] 沒有人在裡面")
                return
            # 創建一個任務列表，用來存放移動成員的任務
            tasks = []
            # 遍歷源頻道的所有成員，將他們移動到目標頻道的任務加入到任務列表中
            for member in source.members:
                tasks.append(member.move_to(target))
            # 使用asyncio.gather函式來同時執行所有的任務，並等待它們完成
            await asyncio.gather(*tasks)
            # 回覆成功訊息
            await ctx.respond(f"已將 [{source.name}] 的所有人移動到 [{target.name}] ") 
        else:
            await ctx.respond("你沒有管理者權限用來執行這個指令") 

    #創建身分組並且添加文字和語音頻道
    @commands.slash_command(description="創建身分組並且添加文字和語音頻道")
    @discord.option("name", type=discord.SlashCommandOptionType.string, description="身分組名稱")
    async def role(self, ctx, name: str):
        guild = ctx.guild
        role = await guild.create_role(name=name)
        category = await guild.create_category(name)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            role: discord.PermissionOverwrite(read_messages=True),
        }
        await category.create_text_channel(name, overwrites=overwrites)
        await category.create_voice_channel(name, overwrites=overwrites)
        await ctx.respond("完成")

    @commands.slash_command(description="讓mumei告訴你該不該買") 
    async def buy_or_not(self,ctx):
        buyornot = choice(self.jdata['buyornot'])
        await ctx.respond(buyornot)    

    @commands.slash_command(description="傳送訊息至指定伺服器的指定頻道")
    @discord.option("message", type=discord.SlashCommandOptionType.string, description="要傳送的訊息")
    @discord.option("guild_name", type=discord.SlashCommandOptionType.string, description="伺服器名稱")
    @discord.option("channel_name", type=discord.SlashCommandOptionType.string, description="頻道名稱")
    async def message(self, ctx, message: str, guild_name: str, channel_name: str):
        if ctx.author.guild_permissions.administrator:
            guild = discord.utils.find(lambda g: g.name == guild_name, self.bot.guilds)
            if guild is None:
                return await ctx.respond("未找到伺服器!")
        
            channel = discord.utils.find(lambda c: c.name == channel_name, guild.text_channels)
            if channel is None: 
                 return await ctx.respond("未找到頻道!")
         
            try:
                await channel.send(message)
                await ctx.respond(f"訊息已成功發送至 {guild.name} 的 {channel} 頻道!") 
            except:
                await ctx.respond("訊息發送錯誤！")
        else:
            await ctx.respond("你沒有管理者權限用來執行這個指令") 

def setup(bot):
    bot.add_cog(Commands(bot))
