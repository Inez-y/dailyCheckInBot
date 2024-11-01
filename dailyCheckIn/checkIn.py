import discord
from discord.ext import tasks, commands
import datetime
import json
from dotenv import load_dotenv
import os
import pytz

# -----------------------------------
#          Initialize Bot           
# -----------------------------------
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

# Save data as json
def save_checkin_data():
    try:
        with open('checkins.json', 'w') as file:
            json.dump(checkin_data, file)
        print_with_timestamp("Data saved successfully.")
    except Exception as e:
        print_with_timestamp(f"Error saving data: {e}")

# Helper function to state timestamp for print lines
def print_with_timestamp(message):
    # Define the time zones
    server_timezone = pytz.timezone('US/Eastern')  
    local_timezone = pytz.timezone('US/Pacific') 

    # Get the current time in the server's time zone and convert it to the local time zone
    server_time = datetime.datetime.now(server_timezone)
    local_time = server_time.astimezone(local_timezone)

    timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    
# Helper function to get the current month
def get_current_month():
    return datetime.datetime.now().strftime("%Y-%m")

@bot.event
async def on_ready():
    print_with_timestamp(f'{bot.user.name} has connected to Discord!')
    if not monthly_reset.is_running():
        print_with_timestamp("Monthly reset function starting")
        monthly_reset.start()

# -----------------------------------
#           Monthly Reset            
# -----------------------------------
@bot.command(name='admin_monthly_reset_trigger_manually')
@commands.has_role('Admin')
async def trigger_monthly_reset(ctx):
    await run_monthly_reset()  
    await ctx.send("Monthly reset triggered manually!")

# Auto trigger
@tasks.loop(time=datetime.time(hour=0, minute=0))  
async def monthly_reset():
    print_with_timestamp("Checking for monthly reset...")
    now = datetime.datetime.now()
    if now.day == 1 and now.hour == 0:
        await run_monthly_reset() 

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

    print_with_timestamp("Monthly reset completed. Saving data...")
    save_checkin_data()
    print_with_timestamp(f"Monthly check-ins have been reset for the new month: {current_month}")

# -----------------------------------
#           Check In            
# -----------------------------------
@bot.command(name='checkin')
async def checkin(ctx):
    user_id = str(ctx.author.id)
    nickname = ctx.author.display_name  
    current_time = datetime.datetime.now()
    current_month = get_current_month()

    # Initialize user data if not present
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
        print_with_timestamp("New month check-in data")
        checkin_data[user_id] = {
            "nickname": nickname,
            "checkins": 0,
            "last_checkin": checkin_data[user_id]["last_checkin"],
            "month": current_month
        }

    last_checkin_date = checkin_data[user_id]["last_checkin"]
    if last_checkin_date == current_time.strftime("%Y-%m-%d"):
        await ctx.send(f'{ctx.author.mention}, you have already checked in today!')
        return

    # Update check-in data
    print_with_timestamp(f"Updating daily check-in data for {nickname}")
    checkin_data[user_id]["checkins"] += 1
    checkin_data[user_id]["last_checkin"] = current_time.strftime("%Y-%m-%d")
    checkin_data[user_id]["nickname"] = nickname  # Update nickname if changed
    print_with_timestamp(f"Saving daily check-in data for {nickname}.")
    save_checkin_data()

    await ctx.send(f'{ctx.author.mention}, you have successfully checked in for today! Total check-ins this month: {checkin_data[user_id]["checkins"]}')

# -----------------------------------
#           Rankings           
# -----------------------------------
@bot.command(name='prev_ranking')
async def prev_rankings(ctx):
    print_with_timestamp("Previous rankings function is called")
    previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

    if "monthly_history" in checkin_data and previous_month in checkin_data["monthly_history"]:
        # Sort users by number of check-ins
        rankings = sorted(
            checkin_data["monthly_history"][previous_month].items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Limit to the top 10 users
        top_rankings = rankings[:min(10, len(rankings))]

        if top_rankings:
            leaderboard = "\n".join(
                [
                    f"{'🥇' if index == 0 else '🥈' if index == 1 else '🥉' if index == 2 else f'{index + 1}. '} {checkin_data[user_id]['nickname']}: {checkins} check-ins"
                    for index, (user_id, checkins) in enumerate(top_rankings)
                ]
            )
            await ctx.send(f"## Previous Month's Check-In Leaderboard ({previous_month})\n{leaderboard}")
        else:
            await ctx.send(f"No check-ins for {previous_month}!")
    else:
        await ctx.send(f"No data available for {previous_month}!")


@bot.command(name='winners')
async def print_winners(ctx):
    print_with_timestamp("Print winners function is called")
    previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

    if "monthly_history" in checkin_data and previous_month in checkin_data["monthly_history"]:
        rankings = sorted(
            checkin_data["monthly_history"][previous_month].items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Filter out users with the Admin role and get their member objects
        filtered_rankings = []
        for user_id, checkins in rankings:
            member = ctx.guild.get_member(int(user_id))
            if member and not any(role.name == "Admin" for role in member.roles):
                filtered_rankings.append((user_id, checkins, checkin_data[user_id]['nickname']))

        # Build the final top ranking with proper rank placement for ties
        top_rankings = []
        current_rank = 1
        last_checkins = None
        places_collected = 0

        for i, (user_id, checkins, nickname) in enumerate(filtered_rankings):
            # Assign rank based on check-in count
            if last_checkins is None or checkins != last_checkins:
                current_rank = places_collected + 1

            # Collect users for each of the top 3 ranks and their ties
            if current_rank <= 3:
                top_rankings.append((current_rank, user_id, checkins, nickname))
                last_checkins = checkins
                places_collected += 1 if current_rank > places_collected else 0
            else:
                if current_rank > 3 and last_checkins != checkins:
                    break

        if top_rankings:
            leaderboard = "\n".join(
                [
                    f"{'🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else f'{rank}.'} {nickname}: {checkins} check-ins"
                    for rank, user_id, checkins, nickname in top_rankings
                ]
            )
            await ctx.send(f"## Previous Month({previous_month})'s Top 3 Check-In Winners (excluding Admins)\n{leaderboard}")
        else:
            await ctx.send(f"No eligible winners for {previous_month}!")
    else:
        await ctx.send(f"No data available for {previous_month}!")

@bot.command(name='ranking')
async def rankings(ctx):
    print_with_timestamp("Current rankings function is called")
    current_month = get_current_month()

    # Sort users by number of check-ins in the current month
    rankings = sorted(
        [
            (user_id, data["checkins"], data["nickname"]) for user_id, data in checkin_data.items()
            if data.get("month") == current_month and data["checkins"] > 0
        ],
        key=lambda x: x[1],
        reverse=True
    )

    # Limit the leaderboard to the top 10 users
    top_rankings = rankings[:min(10, len(rankings))]

    if top_rankings:
        leaderboard = "\n".join(
            [
                f"{'🥇' if index == 0 else '🥈' if index == 1 else '🥉' if index == 2 else f'{index + 1}. '} {nickname}: {checkins} check-ins"
                for index, (user_id, checkins, nickname) in enumerate(top_rankings)
            ]
        )
        await ctx.send(f"## Current Month's Check-In Leaderboard ({current_month})\n{leaderboard}")
    else:
        await ctx.send(f"No check-ins for this month yet!")

# Run the program
bot.run(TOKEN)
