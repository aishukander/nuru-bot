import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json
import random
import os

class words(Cog_Extension):

    def __init__(self, bot):
        self.bot = bot
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.words_json_path = os.path.join(root_dir, "json\\words.json")
        with open(self.words_json_path,"r",encoding="utf8") as f:
            self.words = json.load(f)
    
    @commands.command()
    async def words(self, ctx, action: str, word):
        if ctx.author.guild_permissions.administrator:
            if action.lower() == "remove":
                if word in self.words:
                    del self.words[word]
                    with open(self.words_json_path, "w") as f:
                        json.dump(self.words, f)
                    await ctx.send(f"刪除偵測: {word}")

            elif action.lower() == "add":
                if word not in self.words:
                    await ctx.send(f"新增偵測: {word}")
                    self.words[word] = "0"
                    with open(self.words_json_path, "w") as f: 
                        json.dump(self.words, f)
            else:
                await ctx.send("無效的動作參數, 請使用 `remove` 或 `add`")
        else:
            await ctx.send("你沒有管理者權限用來執行這個指令")

    @commands.command()
    async def show(self, ctx):
        color = random.randint(0, 16777215)
        embed = discord.Embed(title="Words Count", color=color)
        for word, count in self.words.items():
            embed.add_field(name=word, value=count)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        for word in self.words:
            if word in message.content:
                self.words[word] = str(int(self.words[word]) + 1)
        with open(self.words_json_path, "w") as f:
            json.dump(self.words, f)

async def setup(bot):
    await bot.add_cog(words(bot))