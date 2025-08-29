import discord
from discord.ext import commands
import re
import asyncio
import random
import tomllib
from pathlib import Path
from functools import wraps

toml_dir = Path(__file__).resolve().parents[1] / "toml"
CallPicture_dir = Path(__file__).resolve().parents[1] / "CallPicture"

class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open(toml_dir / "Setting.toml", "rb") as tfile:
            self.Setting = tomllib.load(tfile)

    @staticmethod
    def Guild_Admin_Examine(func):
            @wraps(func)
            async def wrapper(self, ctx, *args, **kwargs):
                try:
                    if ctx.author.guild_permissions.administrator:
                        return await func(self, ctx, *args, **kwargs)
                    else:
                        await ctx.respond("你沒有管理者權限用來執行這個指令", ephemeral=True)
                except AttributeError:
                    await ctx.respond("你不在伺服器內")
            return wrapper

    def picture_autocomplete(ctx: discord.AutocompleteContext):
        query = ctx.value.lower()
        options = [
            discord.OptionChoice(
                name=pic_name, 
                value=str(entry.relative_to(CallPicture_dir))
            )
            for entry in CallPicture_dir.rglob("*") 
            if entry.is_file() and entry.name != "README.md"
            for pic_name in [
                str(entry.relative_to(CallPicture_dir))
                .replace("/", " ")
                .replace("\\", " ")
                .rsplit(".", 1)[0]
            ]
            if query in pic_name.lower()
        ][:25]
        return options

    #刪除所選數量的訊息
    @commands.slash_command(description="刪除所選數量的訊息")
    @discord.option(
        "num", 
        type=discord.SlashCommandOptionType.integer, 
        description="要刪除的訊息數量"
    )
    @Guild_Admin_Examine
    async def delete_msg(self, ctx, num: int):
        await ctx.respond(f"準備開始刪除 {num} 則訊息", ephemeral=True)
        try:
            await ctx.channel.purge(limit=num)
        except Exception as e:
            await ctx.edit(content=f"刪除訊息時發生錯誤: {e}")
        else:
            await ctx.edit(content=f"成功刪除了 {num} 則訊息。")

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
        await ctx.respond("完成", ephemeral=True)

    @commands.slash_command(
        description="讓nuru告訴你該不該買",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    ) 
    async def buy_or_not(self,ctx):
        Buy_OR_Not = random.choice(self.Setting["Buy_OR_Not"])
        await ctx.respond(Buy_OR_Not, ephemeral=True)    

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
        await ctx.respond(new_text, ephemeral=True)

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
        try:
            file_path = CallPicture_dir / picture
            if not file_path.is_file():
                raise FileNotFoundError
        except Exception:
            await ctx.respond("找不到該圖片", ephemeral=True)
            return
        await ctx.respond(file=discord.File(file_path, filename=file_path.name))

def setup(bot):
    bot.add_cog(Message(bot))