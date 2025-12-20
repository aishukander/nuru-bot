import discord
from discord.ext import commands
import tomllib
from pathlib import Path
import random

toml_dir = Path(__file__).resolve().parents[1] / "toml"

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open(toml_dir / "Help.toml", "rb") as tfile:
            self.help_data = tomllib.load(tfile)

    help_symbol ="🔧為伺服器管理員限定\n\
                        🪪為機器人擁有者限定\n\
                        🚹為個人應用時可用\n\
                        🔍為帶有搜尋功能\n\
                        🪧為機器人的回應可被其他人看見"

    @commands.slash_command(
        description="顯示幫助選單",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    async def help(self, ctx):
        color = random.randint(0, 16777215)
        embed = discord.Embed(title="Help menu🗒️", color=color)
        embed.add_field(name="符號說明", value=self.help_symbol,inline=False)
        embed.add_field(name="請使用選單選擇指令類別（指令中的空格會被替換為下劃線）", value="", inline=False)
        await ctx.respond(embed=embed, view=main_help(self.help_data), ephemeral=True)

class main_help(discord.ui.View):
    def __init__(self, help_data: dict):
        super().__init__()
        self.help_data = help_data
        options = [
            discord.SelectOption(
                label=section,
                # Get category.explain or return to the default when it is not available
                description=data.get("category", {}).get("explain", "這裡沒有留下什麼。")
            ) for section, data in self.help_data.items()
        ]
        select = self.children[0]
        if isinstance(select, discord.ui.Select):
            select.options = options

    @discord.ui.select(
        placeholder = "選擇一個類別！",
        min_values = 1,
        max_values = 1,
    )
    async def select_callback(self, select, interaction):
        # Find the selected option to get its description
        selected_option = discord.utils.get(select.options, value=select.values[0])
        description = selected_option.description if selected_option else ""

        color = random.randint(0, 16777215)
        embed = discord.Embed(title=select.values[0], color=color)
        embed.add_field(name="符號說明", value=Help.help_symbol,inline=False)
        embed.add_field(name=description, value="", inline=False)
        await interaction.response.edit_message(embed=embed, view=category_help(self.help_data, select.values[0]))

class category_help(discord.ui.View):
    def __init__(self, help_data: dict, category: str):
        super().__init__()
        self.help_data = help_data
        self.category = category
        # Get the category data
        category_data = self.help_data.get(self.category, {})

        options = [discord.SelectOption(label="help menu", description="返回類別選單")]
        options.extend(
            discord.SelectOption(
                label=section,
                description=""
            ) for section in category_data.keys() if section != "category"
        )
        select = self.children[0]
        if isinstance(select, discord.ui.Select):
            select.options = options

    @discord.ui.select(
        placeholder = "選擇一個指令！",
        min_values = 1,
        max_values = 1,
    )
    async def select_callback(self, select, interaction):
        # If "help menu" is selected, return to the main help menu
        if select.values[0] == "help menu":
            color = random.randint(0, 16777215)
            embed = discord.Embed(title="Help menu🗒️", color=color)
            embed.add_field(name="符號說明", value=Help.help_symbol,inline=False)
            embed.add_field(name="請使用選單選擇指令類別（指令中的空格會被替換為下劃線）", value="", inline=False)
            await interaction.response.edit_message(embed=embed, view=main_help(self.help_data))
            return

        # Create the required data for embed
        cmd_data = self.help_data[self.category].get(select.values[0], {})
        explain = cmd_data.get("explain", "這裡沒有留下什麼。")
        template = f"```{cmd_data.get("template", "這裡沒有留下什麼。")}```"
        how_to_use = f"""
                   `[]`和`<>`分別為選填和必填
                   ```{cmd_data.get("how_to_use", "這裡沒有留下什麼。")}```
        """

        color = random.randint(0, 16777215)
        embed = discord.Embed(title=select.values[0], color=color)
        embed.add_field(name="說明：", value=explain, inline=False)
        embed.add_field(name="範本：", value=template, inline=False)
        embed.add_field(name="如何使用：", value=how_to_use, inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

def setup(bot):
    bot.add_cog(Help(bot))
