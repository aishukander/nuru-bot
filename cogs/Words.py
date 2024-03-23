import discord
from discord.ext import commands
from core.classes import Cog_Extension
import random
import modules.json
from modules.json import words_json_path

class Words(Cog_Extension):
    words_dict = modules.json.open_json(words_json_path)

    @commands.command()
    async def words(self, ctx, action: str, word):
        if ctx.author.guild_permissions.administrator:
            if action.lower() == "remove":
                if word in self.words_dict:
                    del self.words_dict[word]
                    modules.json.dump_json(words_json_path, self.words_dict)
                    await ctx.send(f"刪除偵測: {word}")

            elif action.lower() == "add":
                if word not in self.words_dict:
                    await ctx.send(f"新增偵測: {word}")
                    self.words_dict[word] = "0"
                    modules.json.dump_json(words_json_path, self.words_dict)
            else:
                await ctx.send("無效的動作參數, 請使用 `remove` 或 `add`")
        else:
            await ctx.send("你沒有管理者權限用來執行這個指令")

    @commands.command()
    async def show(self, ctx):
        color = random.randint(0, 16777215)
        embed = discord.Embed(title="Words Count", color=color)
        for word, count in self.words_dict.items():
            embed.add_field(name=word, value=count)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        for word in self.words_dict:
            if word in message.content:
                self.words_dict[word] = str(int(self.words_dict[word]) + 1)
        modules.json.dump_json(words_json_path, self.words_dict)

async def setup(bot):
    await bot.add_cog(Words(bot))