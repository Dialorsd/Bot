import discord
from discord.ext import commands, tasks
import asyncio
import sqlite3
from datetime import datetime, timedelta

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents)

# Database setup
conn = sqlite3.connect('reminders.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (
    user_id INTEGER, 
    type TEXT, 
    time TIMESTAMP
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS servers (
    guild_id INTEGER PRIMARY KEY, 
    start_time TIMESTAMP, 
    time_before_boss INTEGER DEFAULT 10
)''')
conn.commit()

# Helper function to get current time
def now():
    return datetime.utcnow()

# Commands
@bot.command()
async def raid(ctx):
    cursor.execute("INSERT INTO reminders VALUES (?, ?, ?)", (ctx.author.id, 'raid', now()))
    conn.commit()
    await ctx.send(f"Raid registered! You'll be reminded in 2 hours.")

@bot.command()
async def bankraid(ctx):
    cursor.execute("INSERT INTO reminders VALUES (?, ?, ?)", (ctx.author.id, 'bankraid', now()))
    conn.commit()
    await ctx.send(f"BankRaid registered! You'll be reminded in 2 hours.")

@bot.command()
async def addserver(ctx, time_before_boss: int = 10):
    cursor.execute("INSERT OR REPLACE INTO servers VALUES (?, ?, ?)", (ctx.guild.id, now(), time_before_boss))
    conn.commit()
    await ctx.send(f"Server added with boss spawn reminders set {time_before_boss} minutes before spawn.")

@bot.command()
async def bosskilled(ctx):
    cursor.execute("INSERT INTO reminders VALUES (?, ?, ?)", (ctx.guild.id, 'boss', now()))
    conn.commit()
    await ctx.send("Boss killed! Next reminder in 1 hour.")

# Background tasks
@tasks.loop(minutes=1)
async def check_reminders():
    current_time = now()
    cursor.execute("SELECT user_id, type FROM reminders WHERE time <= ?", (current_time - timedelta(hours=2),))
    for user_id, reminder_type in cursor.fetchall():
        user = bot.get_user(user_id)
        if user:
            await user.send(f"Your {reminder_type} cooldown is over!")
    cursor.execute("DELETE FROM reminders WHERE time <= ?", (current_time - timedelta(hours=2),))
    conn.commit()

@tasks.loop(minutes=1)
async def check_bosses():
    current_time = now()
    cursor.execute("SELECT guild_id, start_time, time_before_boss FROM servers")
    for guild_id, start_time, time_before_boss in cursor.fetchall():
        elapsed = (current_time - datetime.fromisoformat(start_time)).total_seconds()
        if int(elapsed / 7200) != int((elapsed - 60) / 7200):  # Boss spawns every 2 hours
            guild = bot.get_guild(guild_id)
            if guild:
                channel = guild.text_channels[0]
                await channel.send(f"Boss spawns in {time_before_boss} minutes!")

# Start tasks
@bot.event
async def on_ready():
    check_reminders.start()
    check_bosses.start()
    print(f'Logged in as {bot.user}')

# Run the bot
bot.run('BOT_TOKEN')
