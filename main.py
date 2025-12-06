#各種使用的模組
"""======================================================================================="""
import discord
import random
import tomllib
from pathlib import Path
from functools import wraps
import os
"""======================================================================================="""

intents = discord.Intents.all()

toml_dir = Path(__file__).resolve().parent / "toml"

with open(toml_dir / "Setting.toml", "rb") as tfile:
    Setting = tomllib.load(tfile)

with open(toml_dir / "Token.toml", "rb") as tfile:
    Token = tomllib.load(tfile)

bot = discord.Bot()

# Check user permissions function
def Owner_Examine(func):
    @wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        if ctx.author.id == int(Token['Owner_ID']):
            return await func(ctx, *args, **kwargs)
        else:
            await ctx.respond("你沒有權限執行這個指令", ephemeral=True)
    return wrapper

# Autocomplete for cogs that are not loaded
def Cogs_NotLoaded(ctx: discord.AutocompleteContext):
    if not hasattr(bot, "cogs"):
        return []

    query = ctx.value.lower()
    cogs_path = Path('./cogs')
    CogsList = [file.stem for file in cogs_path.glob('*.py')]

    Only_Exists_NotLoaded = [cog for cog in CogsList if cog not in bot.cogs]
    return [
        discord.OptionChoice(name=pic, value=pic)
        for pic in Only_Exists_NotLoaded
        if pic.lower().startswith(query)
    ]

# Autocomplete for cogs that are loaded
def Cogs_Loaded(ctx: discord.AutocompleteContext):
    if not hasattr(bot, "cogs"):
        return []

    query = ctx.value.lower()
    return [
        discord.OptionChoice(name=pic, value=pic)
        for pic in bot.cogs
        if pic.lower().startswith(query)
    ]

# Load all cogs from the cogs directory
def load_cogs():
    cogs_path = Path('./cogs')
    # Get all Python files in the cogs directory
    CogsList = [file.stem for file in cogs_path.glob('*.py')]
    total = len(CogsList)
    bar_length = 30
    errors = []
    loaded_count = 0

    for filename in CogsList:
        try:
            bot.load_extension(f'cogs.{filename}')
            status = "OK"
            loaded_count += 1
        except Exception as e:
            status = "FAIL"
            errors.append((filename, str(e)))

        filled = int(bar_length * loaded_count / total)
        bar = "█" * filled + "-" * (bar_length - filled)
        # display the loading progress in the terminal
        print(f"Loading cogs: |{bar}| {loaded_count}/{total} {filename} ... {status}   ",
              end="\r", flush=True)

    print()  # Print a new line after the progress bar
    for fname, msg in errors:
        print(f"  ❌ Error loading {fname}: {msg}")

load_cogs()

@bot.event
async def on_ready():
    # Bot ready event
    bot_version = os.getenv('BOT_VERSION') or "development"
    login_message = f"Bot Logged in as {bot.user}"
    version_message = f'>> Startup is {bot_version} <<'
    border = "=" * 40
    print(border)
    print(f"= {login_message.center(len(border) - 4)} =")
    print(f"= {version_message.center(len(border) - 4)} =")
    print(border)

    # Set the bot's presence
    await bot.change_presence(
        activity = discord.Activity(
            type = discord.ActivityType.watching,
            name = f"@nuru的訊息 | V : {bot_version}"
        )
    )

# Slash command group for cogs management
"""======================================================================================="""
cogs = discord.SlashCommandGroup("cogs", "cogs management instructions")

@cogs.command(description="加載指定的cog")
@discord.option(
    "extension",
    type=discord.SlashCommandOptionType.string,
    description="cogs名稱",
    autocomplete = Cogs_NotLoaded
)
@Owner_Examine
async def load(ctx, extension: str):
    try:
        bot.load_extension(f"cogs.{extension}")
        await ctx.respond(f"{extension}模塊加載完成", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"加載模塊時發生錯誤: {e}", ephemeral=True)

@cogs.command(description="卸載指定的cog")
@discord.option(
    "extension",
    type=discord.SlashCommandOptionType.string,
    description="cogs名稱",
    autocomplete = Cogs_Loaded
)
@Owner_Examine
async def unload(ctx, extension: str):
    try:
        bot.unload_extension(f"cogs.{extension}")
        await ctx.respond(f"{extension}模塊卸載完成", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"卸載模塊時發生錯誤: {e}", ephemeral=True)

@cogs.command(description="重載指定的cog")
@discord.option(
    "extension",
    type=discord.SlashCommandOptionType.string,
    description="cogs名稱",
    autocomplete = Cogs_Loaded
)
@Owner_Examine
async def reload(ctx, extension: str):
    try:
        bot.reload_extension(f"cogs.{extension}")
        await ctx.respond(f"{extension}模塊重載完成", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"重載模塊時發生錯誤: {e}", ephemeral=True)

@cogs.command(description="列出已載入的cog")
@Owner_Examine
async def show(ctx):
    try:
        loaded_cogs = [cog for cog in bot.cogs]
    except AttributeError:
        loaded_cogs = None

    if not loaded_cogs:
        await ctx.respond("目前沒有已載入的 cog", ephemeral=True)
        return

    message = "已載入的 cog 如下：\n"
    for cog in loaded_cogs:
        message += f"• {cog}\n"
    await ctx.respond(message, ephemeral=True)

bot.add_application_command(cogs)
"""======================================================================================="""

# Ping command to test bot latency
@bot.command(
    description="測試bot的延遲",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install
    }
)
async def ping(ctx):
    await ctx.respond(f"{round(bot.latency*1000)}(ms)", ephemeral=True)

# Command to get the bot's invitation link
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
