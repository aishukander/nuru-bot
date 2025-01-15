#各種使用的模組
"""======================================================================================="""
import discord
import random
import json
from pathlib import Path
from functools import wraps
"""======================================================================================="""

intents = discord.Intents.all()

json_dir = Path(__file__).resolve().parent / "json"

with open(json_dir / "Setting.json", "r", encoding="utf8") as jfile:
    Setting = json.load(jfile)

with open(json_dir / "Token.json", "r", encoding="utf8") as jfile:
    Token = json.load(jfile)

bot = discord.Bot()

def Guild_Admin_Examine(func):
    @wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        try:
            if ctx.author.guild_permissions.administrator:
                return await func(ctx, *args, **kwargs)
            else:
                await ctx.respond("你沒有管理者權限用來執行這個指令")
        except AttributeError:
            await ctx.respond("你不在伺服器內")
    return wrapper

def Cogs_NotLoaded(ctx: discord.AutocompleteContext):
    query = ctx.value.lower()
    cogs_path = Path('./cogs')
    CogsList = [file.stem for file in cogs_path.glob('*.py')]

    Cogs_Loaded = []
    try:
        for cog in [cog for cog in bot.cogs]:
            Cogs_Loaded.append(cog)
    except AttributeError:
        pass

    Only_Exists_NotLoaded = [cog for cog in CogsList if cog not in Cogs_Loaded]
    return [
        discord.OptionChoice(name=pic, value=pic)
        for pic in Only_Exists_NotLoaded
        if pic.lower().startswith(query)
    ]
    
def Cogs_Loaded(ctx: discord.AutocompleteContext):
    query = ctx.value.lower()
    Cogslist = []
    try:
        for cog in [cog for cog in bot.cogs]:
            Cogslist.append(cog)
    except AttributeError:
        pass
    return [
        discord.OptionChoice(name=pic, value=pic)
        for pic in Cogslist
        if pic.lower().startswith(query)
    ]

#載入所有位於cogs的cog
def load_cogs():
    cogs_path = Path('./cogs')
    CogsList = [file.stem for file in cogs_path.glob('*.py')]
    for filename in CogsList:
        bot.load_extension(f'cogs.{filename}')
        print(f"載入 {filename} 完成")

load_cogs()

@bot.event
async def on_ready():

    #啟動時會在終端機印出的訊息
    bot_name = f"Bot Logged in as {bot.user}"
    border = "=" * 40
    print(border)
    print(f"= {bot_name.center(len(border) - 4)} =")
    print(f"= {'>>  Bot start  <<'.center(len(border) - 4)} =")
    print(border)

    #bot的狀態顯示
    await bot.change_presence(activity=discord.Game(name="/help general 來獲取指令列表"))

#用於加載、卸載、重讀不同cosg檔
"""======================================================================================="""
cogs = discord.SlashCommandGroup("cogs", "cogs management instructions")

@cogs.command(
    description="加載指定的cog"
)
@discord.option(
    "extension", 
    type=discord.SlashCommandOptionType.string, 
    description="cogs名稱", 
    autocomplete = Cogs_NotLoaded
)
@Guild_Admin_Examine
async def load(ctx, extension: str):
    try:
        bot.load_extension(f"cogs.{extension}")
        await ctx.respond(f"{extension}模塊加載完成")
    except Exception as e:
        await ctx.respond(f"加載模塊時發生錯誤: {e}")

@cogs.command(
    description="卸載指定的cog"
)
@discord.option(
    "extension", 
    type=discord.SlashCommandOptionType.string, 
    description="cogs名稱", 
    autocomplete = Cogs_Loaded
)
@Guild_Admin_Examine
async def unload(ctx, extension: str):
    try:
        bot.unload_extension(f"cogs.{extension}")
        await ctx.respond(f"{extension}模塊卸載完成")
    except Exception as e:
        await ctx.respond(f"卸載模塊時發生錯誤: {e}")

@cogs.command(
    description="重載指定的cog"
)
@discord.option(
    "extension", 
    type=discord.SlashCommandOptionType.string, 
    description="cogs名稱", 
    autocomplete = Cogs_Loaded
)
@Guild_Admin_Examine
async def reload(ctx, extension: str):
    try:
        bot.reload_extension(f"cogs.{extension}")
        await ctx.respond(f"{extension}模塊重載完成")
    except Exception as e:
        await ctx.respond(f"重載模塊時發生錯誤: {e}")

@cogs.command(
    description="列出已載入的cog"
)
@Guild_Admin_Examine
async def list(ctx):
    loaded_cogs = Cogs_Loaded()
    message = "已載入的 cog 如下：\n"
    for cog in loaded_cogs:
        message += f"* {cog}\n"
    await ctx.respond(message)

bot.add_application_command(cogs)
"""======================================================================================="""

#測試bot的ping值
@bot.command(
    description="測試bot的延遲",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    }
)
async def ping(ctx):
    await ctx.respond(f"{round(bot.latency*1000)}(ms)")

#用來取得bot的邀請連結
@bot.command(
    description="取得邀請連結",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    }
)
async def invitation(ctx):
    color = random.randint(0, 16777215)
    embed=discord.Embed(title="------連結------", url=Setting["Invitation"], description="狠狠的點下去吧", color=color)
    await ctx.respond(embed=embed)

if __name__ == "__main__":
    bot.run(Token["Bot_Token"])
