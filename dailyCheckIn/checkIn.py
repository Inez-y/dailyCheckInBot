import discord
from discord.ext import tasks, commands
import datetime
import json
from dotenv import load_dotenv
import os

intents = discord.Intents.default()
intents.message_content = True  
intents.members = True    

load_dotenv() # for ubuntu aws
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='/', intents=intents)

# load check-in data
try:
    with open('checkins.json', 'r') as file:
        checkin_data = json.load(file)
except FileNotFoundError:
    checkin_data = {}

def save_checkin_data():
    with open('checkins.json', 'w') as file:
        json.dump(checkin_data, file)

# Helper function to get the current month (e.g., "2024-09")
def get_current_month():
    return datetime.datetime.now().strftime("%Y-%m")

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='checkin')
async def checkin(ctx):
    user_id = str(ctx.author.id)
    current_time = datetime.datetime.now()
    current_month = get_current_month()

    if user_id not in checkin_data:
        checkin_data[user_id] = {"checkins": 0, "last_checkin": "", "month": current_month}

    if checkin_data[user_id]["month"] != current_month:
        checkin_data[user_id] = {"checkins": 0, "last_checkin": "", "month": current_month}

    last_checkin_date = checkin_data[user_id]["last_checkin"]
    if last_checkin_date == current_time.strftime("%Y-%m-%d"):
        await ctx.send(f'{ctx.author.mention}, you have already checked in today!')
        return

    checkin_data[user_id]["checkins"] += 1
    checkin_data[user_id]["last_checkin"] = current_time.strftime("%Y-%m-%d")
    save_checkin_data()

    await ctx.send(f'{ctx.author.mention}, you have successfully checked in for today! Total check-ins this month: {checkin_data[user_id]["checkins"]}')

@bot.command(name='rankings')
async def rankings(ctx):
    # Sort users by number of check-ins in the current month
    current_month = get_current_month()
    rankings = sorted(
        [(user_id, data["checkins"]) for user_id, data in checkin_data.items() if data["month"] == current_month],
        key=lambda x: x[1],
        reverse=True
    )

    if rankings:
        leaderboard = "\n".join([f"**{index + 1}.** <@{user_id}>: {checkins} check-ins" for index, (user_id, checkins) in enumerate(rankings)])
        await ctx.send(f"**Monthly Check-In Leaderboard**\n{leaderboard}")
    else:
        await ctx.send("No check-ins for this month yet!")

@tasks.loop(hours=24)  
async def reset_monthly_checkins():
    current_date = datetime.datetime.now()

    if current_date.day == 1:
        current_month = current_date.strftime("%Y-%m")
        previous_month = (current_date.replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

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
        print("Monthly check-ins have been reset for the new month.")

@bot.command(name='prev_rankings')
async def prev_rankings(ctx):
    previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

    if "monthly_history" in checkin_data and previous_month in checkin_data["monthly_history"]:
        rankings = sorted(
            checkin_data["monthly_history"][previous_month].items(),
            key=lambda x: x[1],
            reverse=True
        )

        if rankings:
            leaderboard = "\n".join([f"**{index + 1}.** <@{user_id}>: {checkins} check-ins" for index, (user_id, checkins) in enumerate(rankings)])
            await ctx.send(f"**Previous Month's Check-In Leaderboard ({previous_month})**\n{leaderboard}")
        else:
            await ctx.send(f"No check-ins for {previous_month}!")
    else:
        await ctx.send(f"No data available for {previous_month}!")

@tasks.loop(hours=24)
async def reset_daily_checkins():
    global checkin_data
    checkin_data = {}
    save_checkin_data()
    print("Daily check-ins have been reset.")

@bot.event
async def on_ready():
    if not reset_daily_checkins.is_running():
        reset_daily_checkins.start()

bot.run(TOKEN)
