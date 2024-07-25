import discord
from discord.ext import commands
import requests

class MinecraftStatus(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def mcstatus(self, ctx, server_ip: str, port: int = 25565):
		url = f"https://api.mcsrvstat.us/2/{server_ip}:{port}"
		try:
			response = requests.get(url)
			response.raise_for_status()
			data = response.json()
			if data['online']:
				if 'software' not in data:
					data['software'] = "Vanilla"
				embed = discord.Embed(title="Minecraft 伺服器狀態", color=discord.Color.green())
				embed.add_field(name="伺服器", value=f"{server_ip}:{port}", inline=False)
				embed.add_field(name="玩家數量", value=f"{data['players']['online']}/{data['players']['max']}", inline=False)
				embed.add_field(name="伺服器版本", value=f"{data['version']} {data['software']}", inline=False)
				embed.add_field(name="MOTD", value=''.join(data['motd']['clean']).replace('[', '').replace(']', ''), inline=False)
				await ctx.send(embed=embed)
			else:
				await ctx.send(f"伺服器 {server_ip}:{port} 不在線上")
		except requests.exceptions.RequestException as e:
			await ctx.send(f"無法檢查伺服器狀態: {e}")

def setup(bot):
	bot.add_cog(MinecraftStatus(bot))