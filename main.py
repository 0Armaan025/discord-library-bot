import asyncio
import difflib
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import time
import uuid
import json
import anthropic
import requests

client = anthropic.Anthropic()

start_time = 0

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)


def load_user_data():
    try:
        with open('storehouse.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_user_data():
    with open('storehouse.json', 'w') as f:
        json.dump(user_data, f, indent=4)

user_data = load_user_data()

def get_user_sessions(user_id):
    return user_data.get(str(user_id), {}).get('sessions', [])

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def test(ctx):
    await ctx.send('testing 1 2 3')

@bot.command(aliases=['find-book'])
async def find(ctx):
    await ctx.send(f"Which book are you looking for? {ctx.author.mention}")
    book = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    book = book.content.strip()
    embed = discord.Embed(title=f"Search results for '{book}'", description="Here are some books that match your search:", color=discord.Colour.blurple())
    
    api_url = f"http://127.0.0.1:5000/get-book/{book}"
    response = requests.get(api_url)
    response = response.json()
    
    if not response:
        await ctx.send('Sorry! No books found. Please try another book.')
    else:
        count = 0
        for item in response:
            if count >= 8:  
                break
            
            title = item['title']
            author = item['author']
            year = item['year']
            language = item['language']
            download_link = item['file_link']
            
            book_info = f"**Author:** {author}\n**Year:** {year}\n**Language:** {language}\n**[Download Link]({download_link})**"
            embed.add_field(name=title, value=book_info, inline=False)
            
            count += 1
        
        await ctx.send(embed=embed)

@bot.command(aliases=['help-me'])
async def help_me(ctx):
    await ctx.send("So you need help? huh, that means you didn't read the documentation, very bad of you xD")
    embed = discord.Embed(title="Help", description="Here are some commands that you can use:", color=discord.Colour.dark_magenta())
    embed.add_field(name="$howdy", value="Greets the user", inline=False)
    embed.add_field(name="$farewell", value="Says bye to the user", inline=False)
    embed.add_field(name="$test", value="testing 1 2 3 ", inline=False)
    embed.add_field(name="$find", value="Helps in finding pdf of a book and downloading it directly", inline=False)
    embed.add_field(name="$recommend", value="Recommends a book to the user based on genre", inline=False)
    embed.add_field(name="$read-book", value="Starts your reading session", inline=False)
    embed.add_field(name="$stop-session", value="Stops your ongoing session", inline=False)
    embed.add_field(name="$sessions", value="Shows all your sessions yet", inline=False)
    embed.add_field(name="$leaderboard", value="Shows the leaderboard", inline=False)
    embed.add_field(name="$total-time", value="Shows your total time", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def recommend(ctx):
    await ctx.send(f"What genre of book are you looking for? {ctx.author.mention}")
    genre = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    genre = genre.content.strip()
    message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    temperature=0,
    system="You are an amazing librarian and you help people recommending books",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please recommend me some books in listview, my favorite genre is: " + genre
                }
            ]
        }
    ]
    )
  
    await ctx.send(message.content[0].text)
    

@bot.command(aliases=['hello', 'hi', 'sup'])
async def howdy(ctx):
    await ctx.send(f'Howdy How is it going? {ctx.author.mention}\nMaybe you can read a book? 👀,\n Type ``$read-book`` to get started with your session')

def time_convert(sec):
    mins = sec // 60
    sec %= 60
    hours = mins // 60
    mins %= 60
    return "{0}:{1}:{2}".format(int(hours), int(mins), sec)

def start_user_session(user_id, book_name, book_author):
    global user_data
    session_id = str(uuid.uuid4())
    start_time = time.time()
    
    user_id_str = str(user_id)
    if user_id_str not in user_data:
        user_data[user_id_str] = {
            'username': None,
            'userid': user_id,
            'sessions': []
        }

    user_data[user_id_str]['sessions'].append({
        'sessionId': session_id,
        'startTime': start_time,
        'endTime': None,
        'bookName': book_name,
        'bookAuthor': book_author,
        'timeElapsed': None
    })

    save_user_data()
    return session_id

def stop_user_session(user_id, session_id):
    global user_data
    end_time = time.time()
    user_id_str = str(user_id)
    for session in user_data[user_id_str]['sessions']:
        if session['sessionId'] == session_id:
            session['endTime'] = end_time
            session['timeElapsed'] = end_time - session['startTime']
            break

    save_user_data()

@bot.command(aliases=['bye', 'sayonara','cya','goodbye'])
async def farewell(ctx):
    await ctx.send(f'Goodbye {ctx.author.mention} 🌟\nIt was amazing to have you here today!')

@bot.command(aliases=['read-book', 'read'])
async def start_reading(ctx):
    global start_time
    user_id_str = str(ctx.author.id)
    if user_id_str in user_data and user_data[user_id_str]['sessions']:
        last_session = user_data[user_id_str]['sessions'][-1]
        if last_session['endTime'] is None:
            await ctx.send("You already have an ongoing session. Please stop it before starting a new one.")
            return

    await ctx.send("Which book are you going to read? Can you please list the name of the book.")
    print(f"Sent prompt for book name to {ctx.author}")

    try:
        book_response = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        book_name = book_response.content.strip() 
        print(f"Received book name: {book_name}")

        await ctx.send(f"Great choice. Now, who is the author of '{book_name}'?")
        print(f"Sent prompt for author name to {ctx.author}")

        author_response = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        author_name = author_response.content.strip()  
        print(f"Received author name: {author_name}")
        
        confirmation_message_text = f"Is your book '{book_name}' by '{author_name}'?"
        confirmation_message = await ctx.send(confirmation_message_text)
        print(f"Sent confirmation message: {confirmation_message_text}")

        await confirmation_message.add_reaction("👍")
        print("Added thumbs up reaction to confirmation message")

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=lambda r, u: str(r.emoji) == "👍" and u == ctx.author and r.message.id == confirmation_message.id)
            session_id = start_user_session(ctx.author.id, book_name, author_name)
            user_data[user_id_str]['username'] = ctx.author.name
            save_user_data()
            await ctx.send(f"Your session has started. You're reading '{book_name}' by {author_name}. Enjoy your reading!")
            print(f"Session started for book '{book_name}' by {author_name} with session ID: {session_id}")
        except asyncio.TimeoutError:
            await ctx.send("Sorry, but you didn't respond in time. Please try again later.")
            print("Timeout waiting for thumbs up reaction")
    except asyncio.TimeoutError:
        await ctx.send("Sorry, but you didn't respond in time. Please try again later.")
        print("Timeout waiting for book or author response")

@bot.command(aliases=['stop-session','stop'])
async def stop_session(ctx):
    user_id_str = str(ctx.author.id)
    if user_id_str in user_data and user_data[user_id_str]['sessions']:
        last_session = user_data[user_id_str]['sessions'][-1]
        if last_session['endTime'] is None:
            stop_user_session(ctx.author.id, last_session['sessionId'])
            elapsed_time_str = time_convert(last_session['timeElapsed'])
            await ctx.send(f"Your session lasted for {elapsed_time_str}. Great job!")
            print(f"Session stopped, duration: {elapsed_time_str}")
        else:
            await ctx.send("No active session found. Please start a session first.")
            print("No active session found to stop")
    else:
        await ctx.send("No active session found. Please start a session first.")
        print("No active session found to stop")

@bot.command(aliases=['sessions'])
async def list_sessions(ctx, user: discord.User = None):
    if(user!=None):
        user_id=user.id
    user_id = ctx.author.id
    sessions = get_user_sessions(user_id)
    if sessions:
        response = f"Here are your reading sessions, {ctx.author.mention}:\n"
        for i, session in enumerate(sessions, 1):
            start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session['startTime']))
            end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session['endTime'])) if session['endTime'] else 'Ongoing'
            time_elapsed = time_convert(session['timeElapsed']) if session['timeElapsed'] else 'N/A'
            response += (f"Session {i}:\n"
                         f"- Book: {session['bookName']} by {session['bookAuthor']}\n"
                         f"- Start Time: {start_time}\n"
                         f"- End Time: {end_time}\n"
                         f"- Time Elapsed: {time_elapsed}\n\n")
    else:
        response = f"{ctx.author.mention}, you have no recorded sessions."
    await ctx.send(response)

async def get_total_time(ctx):
    user_id = ctx.author.id
    sessions = get_user_sessions(user_id)
    total_time = sum(session['timeElapsed'] for session in sessions if session['timeElapsed'] is not None)
    return total_time

@bot.command(aliases=['total-time'])
async def total_time(ctx):
    total_time = await get_total_time(ctx)
    if total_time:
        total_time_str = time_convert(total_time)
        await ctx.send(f"Total reading time: {total_time_str}")
    else:
        await ctx.send(f"{ctx.author.mention}, you have no recorded reading time.")    

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        
        entered_command = ctx.message.content.split()[0][1:]

        
        command_names = [command.name for command in bot.commands]
        suggested_commands = difflib.get_close_matches(entered_command, command_names, n=1)

        if suggested_commands:
            suggested_command = suggested_commands[0]
            await ctx.send(f"This is a wrong command. Did you mean `{bot.command_prefix}{suggested_command}`?")
        else:
            await ctx.send("Sorry, I couldn't find any similar commands.")

    
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide all required arguments for the command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please provide arguments of the correct type.")
    else:
        
        print(error)


bot.remove_command('help')



@bot.command()
async def leaderboard(ctx):
    leaderboard_data = []

    for user_id, user_info in user_data.items():
        total_time = sum(session['timeElapsed'] for session in user_info['sessions'] if session['timeElapsed'] is not None)
        if total_time > 0:
            leaderboard_data.append((user_info['username'], total_time))

    leaderboard_data.sort(key=lambda x: x[1], reverse=True)

    if leaderboard_data:
        response = "🏆 Reading Leaderboard 🏆\n\n"
        for rank, (username, total_time) in enumerate(leaderboard_data, 1):
            total_time_str = time_convert(total_time)
            response += f"{rank}. {username} - {total_time_str}\n"
    else:
        response = "No reading sessions recorded yet."

    await ctx.send(response)

bot.run(os.getenv('token'))
