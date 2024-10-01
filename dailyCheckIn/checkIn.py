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
        print("Check in data file opened")
        checkin_data = json.load(file)
except FileNotFoundError:
    print("Check in data file not found")
    checkin_data = {}

def save_checkin_data():
    try:
        with open('checkins.json', 'w') as file:
            json.dump(checkin_data, file)
        print_with_timestamp("Data saved successfully.")
    except Exception as e:
        print_with_timestamp(f"Error saving data: {e}")


# Helper function to state timestamp for print lines
def print_with_timestamp(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    
# Helper function to get the current month
def get_current_month():
    return datetime.datetime.now().strftime("%Y-%m")

@bot.event
async def on_ready():
    print_with_timestamp(f'{bot.user.name} has connected to Discord!')
    if not daily_reset.is_running():
        print_with_timestamp("Daily reset function start")
        daily_reset.start()
    if not monthly_reset.is_running():
        print_with_timestamp("Monthly reset function start")
        monthly_reset.start()

@tasks.loop(hours=1)
async def daily_reset():
    print_with_timestamp("Daily reset function is working now...")
    now = datetime.datetime.now()

    # Reset at midnight
    if now.hour == 0:
        for user_id in checkin_data:
            if "last_checkin" in checkin_data[user_id]:
                checkin_data[user_id]["last_checkin"] = ""  # Reset last daily check-in

        print_with_timestamp("Daily check-ins have been reset at midnight.")
        print_with_timestamp("Saving data...")
        save_checkin_data()
    else:
        print_with_timestamp("It's not time for the daily reset yet.")

async def run_monthly_reset():
    current_month = get_current_month()
    previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

    if "monthly_history" not in checkin_data:
        checkin_data["monthly_history"] = {}

    # Gather the check-ins for the previous month
    monthly_rankings = {user_id: user_data["checkins"] for user_id, user_data in checkin_data.items() if user_data.get("month") == previous_month}

    # Only save non-empty rankings
    if monthly_rankings:
        checkin_data["monthly_history"][previous_month] = monthly_rankings

    # Reset check-ins for the current month
    for user_id in checkin_data:
        if isinstance(checkin_data[user_id], dict) and "month" in checkin_data[user_id]:
            checkin_data[user_id]["checkins"] = 0
            checkin_data[user_id]["month"] = current_month
            checkin_data[user_id]["last_checkin"] = ""

    print_with_timestamp("Monthly reset completed. Saving data...")
    save_checkin_data()
    print_with_timestamp(f"Monthly check-ins have been reset for the new month: {current_month}")

# Mannually trigger
@bot.command(name='admin_monthly_reset_trigger_manually')
@commands.has_role('Admin')
async def trigger_monthly_reset(ctx):
    await run_monthly_reset()  
    await ctx.send("Monthly reset triggered manually!")

# Auto trigger
@tasks.loop(hours=1)
async def monthly_reset():
    print_with_timestamp("Checking for monthly reset...")

    now = datetime.datetime.now()

    # If today is the first day of the month and it's midnight
    if now.day == 1 and now.hour == 0:
        await run_monthly_reset() 
    else:
        print_with_timestamp("It's not the time for the monthly reset yet.")

# @tasks.loop(hours=1) 
# async def monthly_reset():
#     print_with_timestamp("Checking for monthly reset...")
    
#     # Get the current time
#     now = datetime.datetime.now()

#     # If today is the first day of the month and it's midnight
#     if now.day == 1 and now.hour == 0:
#         current_month = get_current_month()
#         previous_month = (now.replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

#         if "monthly_history" not in checkin_data:
#             checkin_data["monthly_history"] = {}

#         monthly_rankings = {user_id: user_data["checkins"] for user_id, user_data in checkin_data.items() if user_data["month"] == previous_month}

#         # Only save non-empty rankings
#         if monthly_rankings:
#             checkin_data["monthly_history"][previous_month] = monthly_rankings

#         # Reset check-ins for the current month
#         for user_id in checkin_data:
#             if isinstance(checkin_data[user_id], dict) and "month" in checkin_data[user_id]:
#                 checkin_data[user_id]["checkins"] = 0
#                 checkin_data[user_id]["month"] = current_month
#                 checkin_data[user_id]["last_checkin"] = ""

#         print_with_timestamp("Monthly reset completed. Saving data...")
#         save_checkin_data()
#         print_with_timestamp(f"Monthly check-ins have been reset for the new month: {current_month}")
#     else:
#         print_with_timestamp("It's not the time for the monthly reset yet.")


@bot.command(name='checkin')
async def checkin(ctx):
    user_id = str(ctx.author.id)
    nickname = ctx.author.display_name  # Get the user's nickname or username
    current_time = datetime.datetime.now()
    current_month = get_current_month()

    # Initialize user data if not present, ensuring 'month' is included
    if user_id not in checkin_data:
        print_with_timestamp("New user!")
        checkin_data[user_id] = {
            "nickname": nickname,
            "checkins": 0,
            "last_checkin": "",
            "month": current_month
        }

    # Reset check-ins for a new month
    if checkin_data[user_id].get("month") != current_month:
        print_with_timestamp("New month check in data")
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
    print_with_timestamp("Update checkin data")
    checkin_data[user_id]["checkins"] += 1
    checkin_data[user_id]["last_checkin"] = current_time.strftime("%Y-%m-%d")
    checkin_data[user_id]["nickname"] = nickname  # Update nickname if changed
    print_with_timestamp("Saving data...")
    save_checkin_data()

    await ctx.send(f'{ctx.author.mention}, you have successfully checked in for today! Total check-ins this month: {checkin_data[user_id]["checkins"]}')

@bot.command(name='prev_rankings')
async def prev_rankings(ctx):
    print_with_timestamp("prev_rankings function is working...")
    previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

    if "monthly_history" in checkin_data and previous_month in checkin_data["monthly_history"]:
        # Sort users by number of check-ins (integer), not as dictionaries
        rankings = sorted(
            checkin_data["monthly_history"][previous_month].items(),
            key=lambda x: x[1],  # Sort by the check-in count (x[1] is an integer)
            reverse=True
        )

        # Limit the leaderboard to the top 10 users
        top_rankings = rankings[:10] 

        if top_rankings:
            leaderboard = "\n".join(
                [f"**{index + 1}.** {checkin_data[user_id]['nickname']}: {checkins} check-ins"
                 for index, (user_id, checkins) in enumerate(top_rankings)]
            )
            await ctx.send(f"**Previous Month's Check-In Leaderboard ({previous_month})**\n{leaderboard}")
        else:
            await ctx.send(f"No check-ins for {previous_month}!")
    else:
        await ctx.send(f"No data available for {previous_month}!")

@bot.command(name='rankings')
async def rankings(ctx):
    print_with_timestamp("Rankings function is working...")
    current_month = get_current_month()

    # Sort users by number of check-ins in the current month, ensuring the 'month' key exists and check-ins are greater than 0
    rankings = sorted(
        [(user_id, data["checkins"], data["nickname"]) for user_id, data in checkin_data.items() if data.get("month") == current_month and data["checkins"] > 0],
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
