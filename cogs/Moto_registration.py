import discord
from discord.ext import commands, tasks
import tomllib
import tomli_w
from pathlib import Path
import datetime
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
import asyncio
import re
from bs4 import BeautifulSoup

toml_dir = Path(__file__).resolve().parents[1] / "toml"

class Moto_registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_and_run_crawler.start()

        with open(toml_dir / "Moto_registration.toml", "rb") as tfile:
            self.moto_data = tomllib.load(tfile)

    def cog_unload(self):
        self.check_and_run_crawler.cancel()

    @tasks.loop(minutes=5)
    async def check_and_run_crawler(self):
        # 重新載入 TOML 檔案以獲取最新設定
        with open(toml_dir / "Moto_registration.toml", "rb") as f:
            config = tomllib.load(f)

        if not config.get("searches"):
            return

        # 檢查日期並更新
        today = datetime.date.today()
        updated = False
        for search in config["searches"]:
            try:
                search_date = datetime.datetime.strptime(search["date"], "%Y-%m-%d").date()
                if search_date < today:
                    print(f"Updating date for user {search['id']} from {search['date']} to {today.strftime('%Y-%m-%d')}")
                    search["date"] = today.strftime("%Y-%m-%d")
                    updated = True
            except (ValueError, KeyError):
                # 如果日期格式不對或鍵不存在，則跳過
                continue
        
        # 如果有更新，則寫回 toml 檔案
        if updated:
            try:
                with open(toml_dir / "Moto_registration.toml", "w", encoding="utf-8") as f:
                    f.write(tomli_w.dumps(config))
            except Exception as e:
                print(f"Error writing to Moto_registration.toml: {e}")

        print("The motorcycle query begins...")
        await self.bot.wait_until_ready() # 確保 bot 已經登入並準備好

        # 在 executor 中執行同步的爬蟲函式，避免阻塞
        loop = asyncio.get_running_loop()
        all_results = await loop.run_in_executor(
            None, self.process_searches
        )

        if all_results:
            print("The motorcycle query has completed..")
            for user_id_str, results in all_results.items():
                try:
                    # 檢查所有查詢結果中是否有任何可報名的場次
                    has_any_slots = any(result.get('slots') for result in results)

                    if not has_any_slots:
                        continue

                    user = await self.bot.fetch_user(int(user_id_str))
                    
                    # 格式化訊息
                    message_parts = [f"Hi {user.mention}, 這是您的機車考照預約查詢結果："]
                    for result in results:
                        if result['slots']:
                            message_parts.append(f"\n📍 **監理站: {result['station']}** (查詢日期: {result['date']})")
                            message_parts.extend(result['slots'])
                    
                    await user.send("\n".join(message_parts))
                except Exception as e:
                    print(f"an error occurred when sending the result to {user_id_str}: {e}")

    @check_and_run_crawler.before_loop
    async def before_crawler(self):
        await self.bot.wait_until_ready()

    def moto_station_autocomplete(self, ctx: discord.AutocompleteContext):
        query = ctx.value
        station_names = self.moto_data["stations"].keys()
        
        filtered_stations = [
            station for station in station_names if query.lower() in station.lower()
        ]

        return [
            discord.OptionChoice(name=station, value=station)
            for station in filtered_stations
        ][:25]
    
    @staticmethod
    def run_crawler(driver, url, license_code, date_str, region_code, station_code, station_name):
        """根據提供的參數執行爬蟲並返回結果"""
        found_slots = []

        # 前往目標網站
        driver.get(url)

        try:
            # 等待頁面加載
            time.sleep(3)

            # --- 與網頁元素互動 ---
            driver.execute_script(f"document.getElementById('licenseTypeCode').value = '{license_code}';")
            driver.execute_script("document.getElementById('licenseTypeCode').dispatchEvent(new Event('change'));")

            # 轉換為民國年
            dt_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            roc_year = dt_obj.year - 1911
            roc_date_str = f"{roc_year}{dt_obj.month:02d}{dt_obj.day:02d}"
        
            date_input = driver.find_element(By.ID, "expectExamDateStr")
            date_input.clear()
            date_input.send_keys(roc_date_str)

            driver.execute_script(f"document.getElementById('dmvNoLv1').value = '{region_code}';")
            driver.execute_script("document.getElementById('dmvNoLv1').dispatchEvent(new Event('change'));")
            time.sleep(1)
            driver.execute_script(f"document.getElementById('dmvNo').value = '{station_code}';")
            driver.execute_script("document.getElementById('dmvNo').dispatchEvent(new Event('change'));")

            search_button = driver.find_element(By.XPATH, "//a[contains(@onclick, 'query();')]")
            search_button.click()
            time.sleep(5)

            try:
                continue_button = driver.find_element(By.XPATH, "//a[text()='選擇場次繼續報名']")
                continue_button.click()
                time.sleep(3)
            except Exception:
                pass # 沒有按鈕也沒關係

            # --- 解析結果 ---
            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table", id="trnTable")
            if table:
                rows = table.find("tbody").find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) == 4 and cols[3].find("a", onclick=lambda x: x and "preAdd" in x):
                        test_date = cols[0].text.strip()
                        description = ' '.join(cols[1].text.strip().split())
                        availability = cols[2].text.strip()
                    
                        slot_info = (
                            f"  - 考試日期: {test_date}\n"
                            f"    場次說明: {description}\n"
                            f"    可報名人數: {availability}"
                        )
                        found_slots.append(slot_info)
        except Exception as e:
            print(f"an error occurred while querying {station_name} ({date_str}): {e}")

        return found_slots
    
    @staticmethod
    def process_searches():
        """
        讀取設定、執行所有爬蟲任務並返回結果。
        """

        with open(toml_dir / "Moto_registration.toml", "rb") as tfile:
            config = tomllib.load(tfile)

        all_results = {}
        license_code = "3"

        # 設定 WebDriver
        options = Options()
        options.add_argument("-headless")
        driver = None # 初始化 driver
        try:
            driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)

            # 遍歷所有搜尋任務
            for search_item in config.get("searches", []):
                user_id = search_item.get("id")
                date_str = search_item.get("date")
                station_name = search_item.get("station")

                if not all([user_id, date_str, station_name]):
                    continue

                station_code = config.get("stations", {}).get(station_name)
                if not station_code:
                    continue
            
                region_code = str((int(station_code) // 10) * 10)

                # 初始化使用者的結果列表
                if user_id not in all_results:
                    all_results[user_id] = []

                # 執行爬蟲
                found_slots = Moto_registration.run_crawler(driver, config["url"], license_code, date_str, region_code, station_code, station_name)
            
                # 儲存結果
                all_results[user_id].append({
                    "station": station_name,
                    "date": date_str,
                    "slots": found_slots
                })
            return all_results
        finally:
            if driver:
                driver.quit()

    @commands.slash_command(description="機車考照預約查詢")
    @discord.option(
        "station", 
        type=discord.SlashCommandOptionType.string, 
        description="哪個監理站", 
        autocomplete=moto_station_autocomplete
    )
    @discord.option(
        "date", 
        type=discord.SlashCommandOptionType.string, 
        description="日期(格式:YYYY-MM-DD)",
    )
    async def moto_registration(self, ctx, station: str, date: str):
        # Validate date format
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            await ctx.respond("日期格式錯誤，請使用 YYYY-MM-DD 格式。", ephemeral=True)
            return
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            await ctx.respond("日期無效，請檢查日期是否正確 (例如月份或日期是否超出範圍)。", ephemeral=True)
            return
        
        if station not in self.moto_data["stations"]:
            await ctx.respond(f"找不到監理站: {station}。請確認名稱是否正確。", ephemeral=True)
            return

        new_search = {
            "id": str(ctx.author.id),
            "date": date,
            "station": station
        }

        if "searches" not in self.moto_data:
            self.moto_data["searches"] = []
        self.moto_data["searches"].append(new_search)

        try:
            with open(toml_dir / "Moto_registration.toml", "w", encoding="utf-8") as tfile:
                tfile.write(tomli_w.dumps(self.moto_data))
                tfile.write("\n")
            await ctx.respond(f"已為您儲存查詢設定：\n- 監理站：{station}\n- 日期：{date}", ephemeral=True)
        except Exception as e:
            print(f"an error occurred while writing to the TOML file: {e}")
            await ctx.respond("儲存設定時發生錯誤，請聯絡管理員。", ephemeral=True)

    @commands.slash_command(description="取消機車考照通知")
    async def cancel_moto_registration(self, ctx):
            user_id_str = str(ctx.author.id)
            original_count = len(self.moto_data.get("searches", []))
            self.moto_data["searches"] = [
                search for search in self.moto_data.get("searches", [])
                if search.get("id") != user_id_str
            ]
            new_count = len(self.moto_data["searches"])

            if new_count < original_count:
                try:
                    with open(toml_dir / "Moto_registration.toml", "w", encoding="utf-8") as tfile:
                        tfile.write(tomli_w.dumps(self.moto_data))
                        tfile.write("\n")
                    await ctx.respond("已取消您的所有機車考照查詢設定。", ephemeral=True)
                except Exception as e:
                    print(f"an error occurred while writing to the TOML file: {e}")
                    await ctx.respond("取消設定時發生錯誤，請聯絡管理員。", ephemeral=True)
            else:
                await ctx.respond("您目前沒有任何機車考照查詢設定。", ephemeral=True)

def setup(bot):
    bot.add_cog(Moto_registration(bot))