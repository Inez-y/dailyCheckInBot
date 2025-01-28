import discord
from discord.ext import tasks, commands
import datetime
import json
from dotenv import load_dotenv
import os
import pytz
from threading import Lock

# -----------------------------------
#          Initialize Bot
# -----------------------------------
load_dotenv() 
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True  
intents.members = True    
bot = commands.Bot(command_prefix='/', intents=intents)

data_lock = Lock()  # Lock to prevent concurrency issues

# Load check-in data
try:
    with open('checkins.json', 'r') as file:
        print("Check-in data file opened.")
        checkin_data = json.load(file)
        print("Loaded check-in data:", checkin_data)
except FileNotFoundError:
    print("Check-in data file not found. Initializing empty data.")
    checkin_data = {}
except json.JSONDecodeError:
    print("Error decoding JSON. Check the file format.")
    checkin_data = {}

# Save data as json
def save_checkin_data():
    try:
        with data_lock:
            with open('checkins.json', 'w') as file:
                json.dump(checkin_data, file, indent=4)
            print_with_timestamp("Data saved successfully.")
    except Exception as e:
        print_with_timestamp(f"Error saving data: {e}")

# Ensure guild data exists
def ensure_guild_data(guild_id):
    if guild_id not in checkin_data:
        checkin_data[guild_id] = {
            "current-month": {},
            "monthly_history": {}
        }

# Helper function to add timestamp to print statements
def print_with_timestamp(message):
    server_timezone = pytz.timezone('US/Eastern')  
    local_timezone = pytz.timezone('US/Pacific') 
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
    print("Registered Commands:", [command.name for command in bot.tree.get_commands()])
    
    if not monthly_reset.is_running():
        print_with_timestamp("Monthly reset function starting.")
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

    with data_lock:
        for guild_id in checkin_data:
            ensure_guild_data(guild_id)
            guild_data = checkin_data[guild_id]

            # Move current month's data to monthly history
            if previous_month in guild_data["current-month"]:
                guild_data["monthly_history"][previous_month] = {
                    user_id: data["checkins"]
                    for user_id, data in guild_data["current-month"][previous_month].items()
                }

            # Reset current-month data for the new month
            guild_data["current-month"] = {current_month: {}}

    save_checkin_data()
    print_with_timestamp(f"Monthly check-ins have been reset for all servers for the new month: {current_month}")

# -----------------------------------
#           Check In
# -----------------------------------
@bot.tree.command(name='checkin', description="Check in for the day.")
async def checkin(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    nickname = interaction.user.display_name
    current_time = datetime.datetime.now()
    current_month = get_current_month()

    ensure_guild_data(guild_id)

    with data_lock:
        guild_data = checkin_data[guild_id]

        # Initialize current month data if it doesn't exist
        if current_month not in guild_data["current-month"]:
            guild_data["current-month"][current_month] = {}

        # Initialize user data if it doesn't exist
        if user_id not in guild_data["current-month"][current_month]:
            guild_data["current-month"][current_month][user_id] = {
                "nickname": nickname,
                "checkins": 0,
                "last_checkin": ""
            }

        # Get user data
        user_data = guild_data["current-month"][current_month][user_id]

        # Check if the user has already checked in today
        if user_data["last_checkin"] == current_time.strftime("%Y-%m-%d"):
            await interaction.response.send_message(f'{interaction.user.mention}, you have already checked in today!')
            return

        # Update user check-in data
        user_data["checkins"] += 1
        user_data["last_checkin"] = current_time.strftime("%Y-%m-%d")
        user_data["nickname"] = nickname

    save_checkin_data()

    await interaction.response.send_message(
        f'{interaction.user.mention}, you have successfully checked in for today! '
        f'Total check-ins this month: {user_data["checkins"]}'
    )

@bot.tree.command(name='ranking', description="View the current month's leaderboard.")
async def rankings(interaction: discord.Interaction):
    # Defer the response immediately to prevent timeout
    await interaction.response.defer()

    guild_id = str(interaction.guild.id)
    current_month = get_current_month()

    # Ensure check-ins exist for this server
    if guild_id not in checkin_data:
        await interaction.followup.send(f"No check-ins for this server yet!")
        return
    elif current_month not in checkin_data[guild_id]["current-month"]:
        await interaction.followup.send(f"No check-ins for this month yet!")
        return

    guild_data = checkin_data[guild_id]
    current_data = guild_data["current-month"][current_month]

    rankings = sorted(
        [
            (user_id, data["checkins"], data["nickname"]) 
            for user_id, data in current_data.items()
        ],
        key=lambda x: x[1],
        reverse=True
    )

    if rankings:
        leaderboard = "\n".join(
            [
                f"{'🥇' if index == 0 else '🥈' if index == 1 else '🥉' if index == 2 else f'{index + 1}. '} {nickname}: {checkins} check-ins"
                for index, (user_id, checkins, nickname) in enumerate(rankings)
            ]
        )
        await interaction.followup.send(f"## Current Month's Check-In Leaderboard ({current_month})\n{leaderboard}")
    else:
        await interaction.followup.send(f"No check-ins for this month yet!")



@bot.tree.command(name='winners')
async def print_winners(interaction: discord.Interaction):
    print_with_timestamp("Print winners function is called")
    guild_id = str(interaction.guild.id)
    previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

    # Ensure the guild and monthly history exist
    if guild_id not in checkin_data or "monthly_history" not in checkin_data[guild_id]:
        await interaction.response.send_message(f"No data available for {previous_month}!")
        return

    guild_data = checkin_data[guild_id]

    # Check if the previous month exists in monthly history
    if previous_month not in guild_data["monthly_history"]:
        await interaction.response.send_message(f"No check-ins for {previous_month}!")
        return

    previous_data = guild_data["monthly_history"][previous_month]

    # Now get the user's nickname from current month's data (fallback)
    current_month = get_current_month()
    current_data = guild_data["current-month"].get(current_month, {})

    # Get rankings for the previous month (only check-ins)
    rankings = sorted(
        [
            (user_id, checkins, current_data.get(user_id, {}).get("nickname", "Unknown"))
            for user_id, checkins in previous_data.items()
        ],
        key=lambda x: x[1],  # Sort by check-ins
        reverse=True
    )

    # Group users by their check-ins count
    grouped_rankings = {}
    for user_id, checkins, nickname in rankings:
        # Exclude users with "Admin" role
        member = interaction.guild.get_member(int(user_id))
        if member and any(role.name == "Admin" for role in member.roles):
            continue

        if checkins not in grouped_rankings:
            grouped_rankings[checkins] = []
        grouped_rankings[checkins].append((user_id, nickname))

    # Build the top rankings list
    top_rankings = []
    current_rank = 1
    for checkins in sorted(grouped_rankings.keys(), reverse=True):
        users_with_same_checkins = grouped_rankings[checkins]
        
        # Add users with the same check-ins under the same rank
        user_list = ", ".join([nickname for _, nickname in users_with_same_checkins])
        top_rankings.append((current_rank, user_list, checkins))

        # Update the rank for the next group of users
        current_rank += 1

        # Limit to top 3
        if len(top_rankings) >= 3:
            break

    # If there are no rankings, handle that case
    if top_rankings:
        leaderboard = "\n".join(
            [
                f"{'🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else f'{rank}.'} {user_list}: {checkins} check-ins"
                for rank, user_list, checkins in top_rankings
            ]
        )
        await interaction.response.send_message(f"## Check-In Event Winners from ({previous_month})\n{leaderboard}")
    else:
        await interaction.response.send_message(f"No check-ins for {previous_month}!")




@bot.tree.command(name='prev_ranking', description="View the previous month's leaderboard.")
async def prev_rankings(interaction: discord.Interaction):
    print_with_timestamp("Previous rankings function is called")
    guild_id = str(interaction.guild.id)
    previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

    # Ensure the guild and monthly history exist
    if guild_id not in checkin_data or "monthly_history" not in checkin_data[guild_id]:
        await interaction.response.send_message(f"No data available for {previous_month}!")
        return

    guild_data = checkin_data[guild_id]

    # Check if the previous month exists in monthly history
    if previous_month not in guild_data["monthly_history"]:
        await interaction.response.send_message(f"No check-ins for {previous_month}!")
        return

    previous_data = guild_data["monthly_history"][previous_month]

    # Now get the user's nickname from current month's data (fallback)
    current_month = get_current_month()
    current_data = guild_data["current-month"].get(current_month, {})

    # Get rankings for the previous month (only check-ins)
    rankings = sorted(
        [
            (user_id, checkins, current_data.get(user_id, {}).get("nickname", "Unknown"))
            for user_id, checkins in previous_data.items()
        ],
        key=lambda x: x[1],  # Sort by check-ins
        reverse=True
    )

    # Only include the top 10
    top_rankings = rankings[:min(10, len(rankings))]

    if top_rankings:
        leaderboard = "\n".join(
            [
                f"{'🥇' if index == 0 else '🥈' if index == 1 else '🥉' if index == 2 else f'{index + 1}. '} {nickname}: {checkins} check-ins"
                for index, (user_id, checkins, nickname) in enumerate(top_rankings)
            ]
        )
        await interaction.response.send_message(f"## Previous Month's Check-In Leaderboard ({previous_month})\n{leaderboard}")
    else:
        await interaction.response.send_message(f"No check-ins for {previous_month}!")

@bot.tree.command(name='hello')
async def prev_rankings(interaction: discord.Interaction):
    print_with_timestamp("Hello called")
    await interaction.response.send_message(f"Hydration is key 💧")

# -----------------------------------
#           Run Bot
# -----------------------------------
bot.run(TOKEN)
