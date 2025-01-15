import discord
from discord.ext import commands
import re
import asyncio
import random
import json
from pathlib import Path
from functools import wraps

json_dir = Path(__file__).resolve().parents[1] / "json"
CallPicture_dir = Path(__file__).resolve().parents[1] / "CallPicture"

class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open(json_dir / "Setting.json", "r", encoding="utf8") as jfile:
            self.Setting = json.load(jfile)

    def Guild_Admin_Examine(func):
            @wraps(func)
            async def wrapper(self, ctx, *args, **kwargs):
                try:
                    if ctx.author.guild_permissions.administrator:
                        return await func(self, ctx, *args, **kwargs)
                    else:
                        await ctx.respond("你沒有管理者權限用來執行這個指令")
                except AttributeError:
                    await ctx.respond("你不在伺服器內")
            return wrapper

    def picture_autocomplete(ctx: discord.AutocompleteContext):
            query = ctx.value.lower()
            options = []
            for entry in CallPicture_dir.rglob('*'):
                if entry.is_file():
                    filename_without_extension = entry.stem
                    options.append(filename_without_extension)
            return [
                discord.OptionChoice(name=pic, value=pic)
                for pic in options
                if pic.lower().startswith(query)
            ][:25]

    #讓機器人覆誦你輸入的訊息
    @commands.slash_command(
        description="讓機器人覆誦你輸入的訊息"
    )
    @discord.option(
        "msg", 
        type=discord.SlashCommandOptionType.string, 
        description="要覆誦的訊息"
    )
    @Guild_Admin_Examine
    async def say(self, ctx, msg: str):
        await ctx.respond(msg)

    #刪除所選數量的訊息
    @commands.slash_command(
        description="刪除所選數量的訊息"
    )
    @discord.option(
        "num", 
        type=discord.SlashCommandOptionType.integer, 
        description="要刪除的訊息數量"
    )
    @Guild_Admin_Examine
    async def delete_msg(self, ctx, num: int):
        await ctx.respond(f"準備開始刪除 {num} 則訊息")
        await asyncio.sleep(1)
        await ctx.channel.purge(limit=num+1)
        await ctx.send(f"已刪除 {num} 則訊息")

    #讓bot私訊你來呈現一個記事本
    @commands.slash_command(
        description="讓bot私訊你來呈現一個記事本",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    async def notebook(self, ctx):
        color = random.randint(0, 16777215)
        user = ctx.author
        embed=discord.Embed(title="這是一個記事本", color=color)
        await user.send(embed=embed)
        await ctx.respond("完成")

    @commands.slash_command(
        description="讓mumei告訴你該不該買",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    ) 
    async def buy_or_not(self,ctx):
        Buy_OR_Not = random.choice(self.Setting['Buy_OR_Not'])
        await ctx.respond(Buy_OR_Not)    

    @commands.slash_command(
        description="傳送訊息至指定伺服器的指定頻道"
    )
    @discord.option(
        "message", 
        type=discord.SlashCommandOptionType.string, 
        description="要傳送的訊息"
    )
    @discord.option(
        "guild_name", 
        type=discord.SlashCommandOptionType.string, 
        description="伺服器名稱"
    )
    @discord.option(
        "channel_name", 
        type=discord.SlashCommandOptionType.string, 
        description="頻道名稱"
    )
    @Guild_Admin_Examine
    async def send_msg(self, ctx, message: str, guild_name: str, channel_name: str):
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

    #Word-Changer功能的整合
    @commands.slash_command(
        description="Word-Changer功能的整合",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    @discord.option(
        "text", 
        type=discord.SlashCommandOptionType.string, 
        description="要修改的文字"
    )
    @discord.option(
        "old_msg", 
        type=discord.SlashCommandOptionType.string, 
        description="要被取代的文字"
    )
    @discord.option(
        "new_msg", 
        type=discord.SlashCommandOptionType.string, 
        description="新的文字"
    )
    async def word_changer(self, ctx, text: str, old_msg: str, new_msg: str):
        new_text = re.sub(old_msg, new_msg, text)
        await ctx.respond(new_text)

    #直接把圖片丟至CallPicture即可。
    @commands.slash_command(
        description="給出你指定的圖片",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    @discord.option(
        "picture", 
        type=discord.SlashCommandOptionType.string, 
        description="哪個圖片", 
        autocomplete=picture_autocomplete
    )
    async def called_figure(self, ctx, picture: str):
            file_path = None
            for file in CallPicture_dir.rglob('*'):
                if file.is_file() and file.name.startswith(picture + "."):
                    file_path = file
                    break
            if file_path is None:
                await ctx.respond("找不到該圖片")
                return
            file = discord.File(file_path, filename=file_path.name)
            await ctx.respond(file=file)

def setup(bot):
    bot.add_cog(Message(bot))