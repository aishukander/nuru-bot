import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json
import random
import modules.json

class Words(Cog_Extension):

    words = modules.json.open_words_json()
    
    @commands.command()
    async def words(self, ctx, action: str, word):
        global words
        if ctx.author.guild_permissions.administrator:
            if action.lower() == "remove":
                if word in words:
                    del words[word]
                    modules.json.dump_words()
                    await ctx.send(f"刪除偵測: {word}")

            elif action.lower() == "add":
                if word not in words:
                    await ctx.send(f"新增偵測: {word}")
                    words[word] = "0"
                    modules.json.dump_words()
            else:
                await ctx.send("無效的動作參數, 請使用 `remove` 或 `add`")
        else:
            await ctx.send("你沒有管理者權限用來執行這個指令")

    @commands.command()
    async def show(self, ctx):
        color = random.randint(0, 16777215)
        embed = discord.Embed(title="Words Count", color=color)
        for word, count in words.items():
            embed.add_field(name=word, value=count)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        for word in words:
            if word in message.content:
                words[word] = str(int(words[word]) + 1)
        modules.json.dump_words()

async def setup(bot):
    await bot.add_cog(Words(bot))