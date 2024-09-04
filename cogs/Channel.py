import discord
from discord.ext import commands
import asyncio

class Channel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #將語音頻道內所有人移動到另一個語音頻道
    @commands.slash_command(description="將語音頻道內所有人移動到另一個語音頻道")
    @discord.option("source", type=discord.SlashCommandOptionType.channel, description="源頻道")
    @discord.option("target", type=discord.SlashCommandOptionType.channel, description="目標頻道")
    async def move_voice(self, ctx, source: discord.VoiceChannel, target: discord.VoiceChannel):
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
    async def create_role(self, ctx, name: str):
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

def setup(bot):
    bot.add_cog(Channel(bot))