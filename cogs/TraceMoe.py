import discord
from discord.ext import commands
import random
import requests
import urllib.parse
import re

class TraceMoe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api.trace.moe/search"

    @commands.slash_command(description="找出圖片在動漫中的位置")
    @discord.option("image", type=discord.SlashCommandOptionType.attachment, description="圖片")
    async def trace_search(self, ctx, image: discord.Attachment):
        await ctx.defer()
        try:
            response = requests.get("https://api.trace.moe/search?cutBorders&url={}"
              .format(urllib.parse.quote_plus(image.url))
            ).json()
            result = response["result"][0]

            Time = f"{round(result['from'] // 60)}分{round(result['from'] % 60):02}秒"
            match = re.search(r'^(?:\[[^\]]+\]\s*)?([^-\[\]]+?)\s*-\s*\d+', result["filename"])
            if match:
                Name = match.group(1).strip()
            else:
                # 如果沒有匹配，使用原始文件名（去除擴展名）
                Name = re.sub(r'\.\w{3,4}$', '', result["filename"])

            color = random.randint(0, 16777215)
            embed=discord.Embed(title="來自trace.moe-api的資訊", color=color)
            embed.add_field(name="動漫名", value=Name, inline=True)
            embed.add_field(name="集數", value=f"第{result['episode']}集", inline=True)
            embed.add_field(name="位置", value=Time, inline=True)
            embed.set_image(url=f"{result['image']}")
            await ctx.respond(embed=embed)
        except Exception as e:
            await ctx.respond(f"指令發生錯誤: {e}")
    
def setup(bot):
    bot.add_cog(TraceMoe(bot))
