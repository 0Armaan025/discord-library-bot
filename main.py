import discord
from discord.ext import commands


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def test(ctx):
    await ctx.send('testing 1 2 3')

@bot.command(aliases=['hello', 'hi', 'sup'])
async def howdy(ctx):
    await ctx.send(f'Howdy! How is it going? {ctx.author.mention}\nMaybe you can read a book? 👀,\n Type ``$read-book`` to get started with your session')

@bot.command(aliases=['bye', 'sayonara','cya','goodbye'])
async def farewell(ctx):
    await ctx.send(f'Goodbye! {ctx.author.mention} 🌟\nIt was amazing to have you here today!')    

bot.run('MTI1MjkxNTk1NjAzMjczNzQ2MQ.GMk2Jx.Mi0rwTG6DQlXC65vkjo_bKBfE3vbf6AqUXOlqo')
