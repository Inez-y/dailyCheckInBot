import discord
from discord.ext import tasks, commands
import datetime
import json
from dotenv import load_dotenv
import os
import asyncio  # To handle sleep

intents = discord.Intents.default()
intents.message_content = True  
intents.members = True    

load_dotenv()  # for ubuntu aws
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='/', intents=intents)

# Load check-in data
try:
    with open('checkins.json', 'r') as file:
        checkin_data = json.load(file)
except FileNotFoundError:
    checkin_data = {}

def save_checkin_data():
    with open('checkins.json', 'w') as file:
        json.dump(checkin_data, file)

# Helper function to get the current month
def get_current_month():
    return datetime.datetime.now().strftime("%Y-%m")

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    if not daily_reset.is_running():
        daily_reset.start()
    if not monthly_reset.is_running():
        monthly_reset.start()

@tasks.loop(hours=24)
async def daily_reset():
    now = datetime.datetime.now()
    # Calculate the time until midnight
    next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_until_midnight = (next_midnight - now).total_seconds()

    # Sleep until midnight
    await asyncio.sleep(time_until_midnight)

    # Reset daily check-ins
    for user_id in checkin_data:
        if "last_checkin" in checkin_data[user_id]:
            checkin_data[user_id]["last_checkin"] = ""  # Reset last daily check-in

    save_checkin_data()
    # print("Daily check-ins have been reset at 00:00.")

# This will run every 24 hours, but we will adjust it to reset only on the 1st of the month
@tasks.loop(hours=24) 
async def monthly_reset():
    now = datetime.datetime.now()
    next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_until_midnight = (next_midnight - now).total_seconds()

    # Sleep until midnight
    await asyncio.sleep(time_until_midnight)

    # If today is the first of the month, reset monthly check-ins
    if now.day == 1:
        current_month = get_current_month()
        previous_month = (now.replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

        if "monthly_history" not in checkin_data:
            checkin_data["monthly_history"] = {}

        monthly_rankings = {user_id: user_data["checkins"] for user_id, user_data in checkin_data.items() if user_data["month"] == previous_month}

        # Only save non-empty rankings
        if monthly_rankings:
            checkin_data["monthly_history"][previous_month] = monthly_rankings

        # Reset check-ins for the current month
        for user_id in checkin_data:
            if isinstance(checkin_data[user_id], dict) and "month" in checkin_data[user_id]:
                checkin_data[user_id]["checkins"] = 0
                checkin_data[user_id]["month"] = current_month
                checkin_data[user_id]["last_checkin"] = ""

        save_checkin_data()
        print(f"Monthly check-ins have been reset for the new month: {current_month}")

@bot.command(name='checkin')
async def checkin(ctx):
    user_id = str(ctx.author.id)
    nickname = ctx.author.display_name  # Get the user's nickname or username
    current_time = datetime.datetime.now()
    current_month = get_current_month()

    # Initialize user data if not present, ensuring 'month' is included
    if user_id not in checkin_data:
        checkin_data[user_id] = {
            "nickname": nickname,
            "checkins": 0,
            "last_checkin": "",
            "month": current_month
        }

    # Reset check-ins for a new month
    if checkin_data[user_id].get("month") != current_month:
        checkin_data[user_id] = {
            "nickname": nickname,
            "checkins": 0,
            "last_checkin": "",
            "month": current_month
        }

    last_checkin_date = checkin_data[user_id]["last_checkin"]
    if last_checkin_date == current_time.strftime("%Y-%m-%d"):
        await ctx.send(f'{ctx.author.mention}, you have already checked in today!')
        return

    # Update check-in data
    checkin_data[user_id]["checkins"] += 1
    checkin_data[user_id]["last_checkin"] = current_time.strftime("%Y-%m-%d")
    checkin_data[user_id]["nickname"] = nickname  # Update nickname if changed
    save_checkin_data()

    await ctx.send(f'{ctx.author.mention}, you have successfully checked in for today! Total check-ins this month: {checkin_data[user_id]["checkins"]}')

@bot.command(name='prev_rankings')
async def prev_rankings(ctx):
    previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

    if "monthly_history" in checkin_data and previous_month in checkin_data["monthly_history"]:
        # Sort users by number of check-ins in descending order
        rankings = sorted(
            checkin_data["monthly_history"][previous_month].items(),
            key=lambda x: x[1]["checkins"],  # Assuming check-ins are stored in a dict with nickname
            reverse=True
        )

        # Limit the leaderboard to the top 10 users
        top_rankings = rankings[:10]  # Slice the top 10

        if top_rankings:
            leaderboard = "\n".join(
                [f"**{index + 1}.** <@{user_id}>: {data['checkins']} check-ins (Nickname: {data['nickname']})"
                 for index, (user_id, data) in enumerate(top_rankings)]
            )
            await ctx.send(f"**Previous Month's Check-In Leaderboard ({previous_month})**\n{leaderboard}")
        else:
            await ctx.send(f"No check-ins for {previous_month}!")
    else:
        await ctx.send(f"No data available for {previous_month}!")

@bot.command(name='rankings')
async def rankings(ctx):
    current_month = get_current_month()

    # Sort users by number of check-ins in the current month, ensuring the 'month' key exists
    rankings = sorted(
        [(user_id, data["checkins"], data["nickname"]) for user_id, data in checkin_data.items() if data.get("month") == current_month],
        key=lambda x: x[1],  # Sort by check-ins
        reverse=True
    )

    # Limit the leaderboard to the top 10 users
    top_rankings = rankings[:10]

    if top_rankings:
        leaderboard = "\n".join([f"**{index + 1}.** {nickname}: {checkins} check-ins"
                                 for index, (user_id, checkins, nickname) in enumerate(top_rankings)])
        await ctx.send(f"**Current Month's Check-In Leaderboard ({current_month})**\n{leaderboard}")
    else:
        await ctx.send(f"No check-ins for this month yet!")

# Run the program
bot.run(TOKEN)
