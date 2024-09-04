import psutil
import time
import random
import discord
from discord.ext import commands

class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="獲取機器人的資訊")
    async def bot_info(self, ctx):
        # 獲取 CPU 使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        # 獲取 RAM 使用情況
        ram_usage = round(psutil.virtual_memory().used / (1024 * 1024))  # 轉換為 MB
        ram_total = round(psutil.virtual_memory().total / (1024 * 1024))  # 轉換為 MB
        ram_percent = psutil.virtual_memory().percent
        # 獲取硬碟使用情況
        disk_total = round(psutil.disk_usage('/').total / (1024 * 1024 * 1024))  # 轉換為 GB
        disk_used = round(psutil.disk_usage('/').used / (1024 * 1024 * 1024))  # 轉換為 GB
        disk_percent = psutil.disk_usage('/').percent
        # 獲取網路使用情況
        net_io_1 = psutil.net_io_counters()
        time.sleep(1)
        net_io_2 = psutil.net_io_counters()
        bytes_sent_per_sec = (net_io_2.bytes_sent - net_io_1.bytes_sent) * 8 / (1024 * 1024)  # 轉換為 Mbps
        bytes_recv_per_sec = (net_io_2.bytes_recv - net_io_1.bytes_recv) * 8 / (1024 * 1024)  # 轉換為 Mbps
        # 獲取系統啟動時間
        boot_time = psutil.boot_time()
        boot_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(boot_time))
        # 獲取 bot 所在的伺服器數量
        guild_count = len(self.bot.guilds)

        # 回應訊息
        color = random.randint(0, 16777215)
        embed=discord.Embed(title="機器人資訊", color=color)
        embed.add_field(name="⚙️CPU 使用率", value=f"{cpu_usage} %", inline=True)
        embed.add_field(name="📦RAM 用量", value=f"{ram_percent} % ({ram_usage} MB / {ram_total} MB)", inline=True)
        embed.add_field(name="💾硬碟使用", value=f"{disk_percent} % ({disk_used} GB / {disk_total} GB)", inline=True)        
        embed.add_field(name="📡網路發收", value=f"{bytes_sent_per_sec:.2f} Mbps / {bytes_recv_per_sec:.2f} Mbps", inline=True)
        embed.add_field(name="⌛系統啟動時間", value=boot_time_str, inline=True)
        embed.add_field(name="🔍所在伺服器數", value=f"{guild_count} 個", inline=True)
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(BotInfo(bot))