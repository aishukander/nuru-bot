import discord
from discord.ext import commands
import random
import requests
import urllib.parse

class AnimeSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        description="找出圖片出自哪部動漫的哪裡(檔案/url擇一)",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    @discord.option(
        "image_file", 
        type=discord.SlashCommandOptionType.attachment, 
        description="圖片檔案", 
        required=False
    )
    @discord.option(
        "image_url", 
        type=discord.SlashCommandOptionType.string, 
        description="圖片連結", 
        required=False
    )
    async def anime_search(self, ctx, image_file: discord.Attachment = None, image_url: str = None):
        await ctx.defer()
        try:
            if image_file:
                url = image_file.url
            elif image_url:
                url = image_url
            else:
                await ctx.respond("請提供圖片檔案或連結")
                return
            response = requests.get("https://api.trace.moe/search?anilistInfo&cutBorders&url={}"
              .format(urllib.parse.quote_plus(url))
            ).json()
            result = response["result"][0]

            Time = f"{round(result['from'] // 60)}分{round(result['from'] % 60):02}秒"

            color = random.randint(0, 16777215)
            embed=discord.Embed(title=result['anilist']['title']['native'], color=color)
            embed.add_field(name="集數", value=f"第{result['episode']}集", inline=True)
            embed.add_field(name="位置", value=Time, inline=True)
            embed.set_image(url=f"{result['image']}")
            embed.set_footer(text="Data from trace.moe API")
            await ctx.respond(embed=embed)
        except Exception as e:
            await ctx.respond(f"指令發生錯誤: {e}")
    
def setup(bot):
    bot.add_cog(AnimeSearch(bot))
