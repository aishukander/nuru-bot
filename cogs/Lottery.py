import discord
from discord.ext import commands
import random


class Lottery(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.lottery_author = None
        self.user_weights = {}

    @commands.command()
    async def lottery(self, ctx, *users: discord.Member):
        self.lottery_author = ctx.author
        self.user_weights = {user: 1 for user in users}
        mentions = ' '.join(user.mention for user in users)
        message = await ctx.send(f'{mentions} 已加入抽籤')
        await message.add_reaction('\u25B6')
        await message.add_reaction('\u2699')

    @commands.command()
    async def weight(self, ctx, user: discord.Member, weight: int):
        self.user_weights[user] = weight
        await ctx.send(f'{user.name} 的權重已設為 {weight}')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user or user != self.lottery_author:
            return

        if str(reaction.emoji) == '\u2699':
            await self.show_weights(reaction.message)
        elif str(reaction.emoji) == '\u25B6':
            await self.draw(reaction.message)

    async def show_weights(self, message):
        weights_text = '\n'.join(f'{user.mention}: {weight}' for user, weight in self.user_weights.items())
        await message.edit(content=f'權重為:\n{weights_text}\n請輸入~weight [欲修改的使用者] [權重] 以修改權重')

    async def draw(self, message):
        total_weight = sum(self.user_weights.values())
        draw = random.randint(1, total_weight)
        for user, weight in self.user_weights.items():
            draw -= weight
            if draw <= 0:
                await message.channel.send(f'{user.mention} 被抽中了!')
                await message.clear_reactions()
                return
        pass

    @commands.command()
    async def weight(self, ctx, user: discord.Member, weight: int):
        self.user_weights[user] = weight
        await ctx.send(f'{user.name} 的權重已設為 {weight}')
        print(self.user_weights)  # 添加這行來檢查 self.user_weights 的狀態

def setup(bot):
    bot.add_cog(Lottery(bot))