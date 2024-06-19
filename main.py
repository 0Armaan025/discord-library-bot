import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

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
    await ctx.send(f'Howdy How is it going? {ctx.author.mention}\nMaybe you can read a book? 👀,\n Type ``$read-book`` to get started with your session')

@bot.command(aliases=['bye', 'sayonara','cya','goodbye'])
async def farewell(ctx):
    await ctx.send(f'Goodbye {ctx.author.mention} 🌟\nIt was amazing to have you here today!')

@bot.command(aliases=['read-book', 'read'])
async def start_reading(ctx):
    await ctx.send("Which book are you going to read? Can you please list the name of the book.")
    
    try:
        
        book_response = await bot.wait_for('message', timeout=30.0)
        book_name = book_response.content 
        
        await ctx.send(f"Great choice. Now, who is the author of '{book_name}'?")
        
        
        author_response = await bot.wait_for('message', timeout=30.0)
        author_name = author_response.content 
        
        
        confirmation_message_text = f"Is your book '{book_name}' by '{author_name}'?"
        confirmation_message = await ctx.send(confirmation_message_text)

        
        await confirmation_message.add_reaction("👍")

        
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=lambda r, u: str(r.emoji) == "👍" and u == ctx.author)
            await ctx.send(f"Your session has started. You're reading '{book_name}' by {author_name}. Enjoy your reading!")
            await start_timer(ctx)
        except asyncio.TimeoutError:
            await ctx.send("Sorry, but you didn't respond in time. Please try again later.")
    except asyncio.TimeoutError:
        await ctx.send("Sorry, but you didn't respond in time. Please try again later.")


async def start_timer(ctx):
    await ctx.send("Your timer has been started")

bot.run(os.getenv('token'))