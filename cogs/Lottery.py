import discord
from discord.ext import commands
from core.classes import Cog_Extension
import random

class Lottery(Cog_Extension):
    lottery_author = None
    user_weights = {}

    @commands.command()
    async def lottery(self, ctx, *users: discord.Member):
        global lottery_author, user_weights
        lottery_author = ctx.author
        user_weights = {user: 1 for user in users}
        mentions = ' '.join(user.mention for user in users)
        message = await ctx.send(f'{mentions} 已加入抽籤')
        await message.add_reaction('\u25B6')
        await message.add_reaction('\u2699')

    @commands.command()
    async def weight(self, ctx, user: discord.Member, weight: int):
        user_weights[user] = weight
        await ctx.send(f'{user.name} 的權重已設為 {weight}')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user != lottery_author or user == self.bot.user:
            return

        if str(reaction.emoji) == '\u2699':
            await self.show_weights(reaction.message)
        elif str(reaction.emoji) == '\u25B6':
            await self.draw(reaction.message)

    async def show_weights(self, message):
        weights_text = '\n'.join(f'{user.mention}: {weight}' for user, weight in user_weights.items())
        await message.edit(content=f'權重為:\n{weights_text}\n請輸入~set_weight [欲修改的使用者] [權重] 以修改權重')

    async def draw(self, message):
        total_weight = sum(user_weights.values())
        draw = random.randint(1, total_weight)
        for user, weight in user_weights.items():
            draw -= weight
            if draw <= 0:
                await message.channel.send(f'{user.mention} 被抽中了!')
                await message.clear_reactions()
                return
        pass

async def setup(bot):
    await bot.add_cog(Lottery(bot))