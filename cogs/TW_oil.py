import discord
from discord.ext import commands, tasks
from playwright.async_api import async_playwright
import random
from datetime import time, datetime
import zoneinfo
import tomllib
import tomli_w
import re

class TW_oil(commands.Cog):
    target_time = time(hour=12, minute=0, tzinfo=zoneinfo.ZoneInfo("Asia/Taipei"))
    def __init__(self, bot):
        self.bot = bot
        self.oil_price_check.start()
        self.oil_data = {}

    def cog_unload(self):
        self.oil_price_check.cancel()

    async def get_oil_prices(self) -> dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
        
            await page.goto("https://gas.goodlife.tw")
        
            try:
                price_Increase = page.locator("#gas-price").first
                price_today = page.locator("#cpc").filter(has_text="今日中油油價")
                await price_Increase.wait_for(state="visible", timeout=5000)
                await price_today.wait_for(state="visible", timeout=5000)

                date_p = price_Increase.locator(".main p").first
                date = await date_p.inner_text()

                if "已公告" in date:
                    date = datetime.now(zoneinfo.ZoneInfo("Asia/Taipei")).strftime("%Y/%m/%d")
                else:
                    date = date.split(",")[0].replace("下週一", "").strip()

                price_future = await price_Increase.locator(".main h2").first.inner_text()
            
                raw_prices = await price_today.locator("ul li").all_inner_texts()
                price_now = [p.replace("\n", "：").replace("油價", "").strip() + "元" for p in raw_prices]

                return {
                    "date": date,
                    "price_future": price_future,
                    "price_now": price_now
                }

            except Exception as e:
                print(f"crawler get a bug: {e}")
                return {}

            finally:
                await browser.close()

    def embed_create(self, price_future, date, price_now) -> discord.Embed:    
        embed = discord.Embed(
            title="⛽ 油價變動通知",
            description=f"預計下週: **{price_future}**",
            color=discord.Color.red() if "漲" in price_future else discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="生效日期", value=date, inline=False)
        embed.add_field(name="今日中油價格", value="\n".join(price_now), inline=False)
        embed.set_footer(text="數據來源：https://gas.goodlife.tw/")
        return embed

    @tasks.loop(time=target_time)
    async def oil_price_check(self):
        self.oil_data = await self.get_oil_prices()

        with open("toml/Oil_Notice.toml", "rb") as f:
            self.oil_setting = tomllib.load(f)

        if self.oil_data["date"] == self.oil_setting.get("data_up"):
            return
        else:
            self.oil_setting["data_up"] = self.oil_data["date"]
            with open("toml/Oil_Notice.toml", "wb") as f:
                tomli_w.dump(self.oil_setting, f)

        if not self.oil_data or "price_future" not in self.oil_data:
            return
        if not self.oil_setting.get("User_IDs"):
            return

        match = re.search(r"(?P<price>\d+\.\d+)", self.oil_data["price_future"])
        if match:
            predicted_value = match.group("price")

            if predicted_value != "0.0":
                try:
                    user_ids = self.oil_setting.get("User_IDs", [])

                    embed = self.embed_create(
                        price_future=self.oil_data["price_future"],
                        date=self.oil_data["date"],
                        price_now=self.oil_data["price_now"]
                    )

                    for user_id in user_ids:
                        user = self.bot.get_user(int(user_id))
                        if user is None:
                            try:
                                user = await self.bot.fetch_user(int(user_id))
                            except:
                                continue
                        
                        if user:
                            try:
                                await user.send(embed=embed)
                            except Exception as dm_e:
                                print(f"Could not send DM to {user_id}: {dm_e}")
                except Exception as e:
                    print(f"Failed to load Oil_Notice.toml or send notifications: {e}")

    @oil_price_check.before_loop
    async def wait_for_ready(self):
        await self.bot.wait_until_ready()

    @commands.slash_command(
        description="獲取油價資訊",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    async def oil_price(self, ctx):
        await ctx.defer()
        oil_data = await self.get_oil_prices()

        if not oil_data:
            await ctx.respond("無法獲取油價資訊，請稍後再試。")
            return

        embed = self.embed_create(
            price_future=oil_data["price_future"],
            date=oil_data["date"],
            price_now=oil_data["price_now"]
        )

        view = QueueControlView(self, ctx)
        await ctx.respond(embed=embed, view=view)

class QueueControlView(discord.ui.View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=30)
        self.cog = cog
        self.ctx = ctx

        with open("toml/Oil_Notice.toml", "rb") as f:
            settings = tomllib.load(f)

        is_subscribed = self.ctx.author.id in settings.get("User_IDs", [])
        label = "取消訂閱油價通知" if is_subscribed else "訂閱油價通知"
        style = discord.ButtonStyle.danger if is_subscribed else discord.ButtonStyle.success
        
        self.button_subscribe = discord.ui.Button(label=label, style=style, custom_id="subscribe_oil")
        self.button_subscribe.callback = self.subscribe_callback
        self.add_item(self.button_subscribe)

    async def subscribe_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("請使用你自己的按鈕！", ephemeral=True)
            return

        try:
            with open("toml/Oil_Notice.toml", "rb") as f:
                settings = tomllib.load(f)
            user_ids = settings.get("User_IDs", [])
        except:
            settings = {"User_IDs": []}
            user_ids = []

        if interaction.user.id in user_ids:
            user_ids.remove(interaction.user.id)
            msg = "已取消訂閱油價變動通知。"
            new_label = "訂閱油價通知"
            new_style = discord.ButtonStyle.success
        else:
            user_ids.append(interaction.user.id)
            msg = "訂閱成功！當油價有變動時，Bot 會私訊通知你。"
            new_label = "取消訂閱油價通知"
            new_style = discord.ButtonStyle.danger

        settings["User_IDs"] = user_ids
        with open("toml/Oil_Notice.toml", "wb") as f:
            tomli_w.dump(settings, f)

        self.button_subscribe.label = new_label
        self.button_subscribe.style = new_style
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(msg, ephemeral=True)

    async def on_timeout(self):
        self.disable_all_items()
        # If there is an original message, update the view to show the disabled buttons
        await self.update_view_on_timeout()

    async def update_view_on_timeout(self):
        try:
            await self.ctx.interaction.edit_original_response(view=self)
        except Exception as e:
            print(f"更新 View 失敗: {e}")

def setup(bot):
    bot.add_cog(TW_oil(bot))