import discord
from discord.ext import commands
import requests
import urllib.parse

class TraceMoe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api.trace.moe/search"

    @commands.slash_command(description='使用圖片搜尋動畫資訊')
    @discord.option("image", type=discord.SlashCommandOptionType.attachment, description="圖片")
    async def trace_search(self, ctx, image: discord.Attachment):
        image_url = image.url
        response = requests.get("https://api.trace.moe/search?cutBorders&url={}"
          .format(urllib.parse.quote_plus(image_url))
        ).json()
    
def setup(bot):
    bot.add_cog(TraceMoe(bot))
