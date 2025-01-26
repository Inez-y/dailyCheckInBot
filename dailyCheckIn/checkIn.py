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
load_dotenv() 
TOKEN = os.getenv('DISCORD_TOKEN')
load_dotenv() 
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True  
intents.members = True    
bot = commands.Bot(command_prefix='/', intents=intents)

# Load check-in data
try:
    with open('checkins.json', 'r') as file:
        print("Check in data file opened")
        checkin_data = json.load(file)
        print("Loaded check-in data:", checkin_data) 
        print("Loaded check-in data:", checkin_data) 
except FileNotFoundError:
    print("Check in data file not found")
    checkin_data = {}
except json.JSONDecodeError:
    print("Error decoding JSON. Check the file format.")
    checkin_data = {}

except json.JSONDecodeError:
    print("Error decoding JSON. Check the file format.")
    checkin_data = {}


# Save data as json
def save_checkin_data():
    try:
        with open('checkins.json', 'w') as file:
            json.dump(checkin_data, file)
        print_with_timestamp("Data saved successfully.")
    except Exception as e:
        print_with_timestamp(f"Error saving data: {e}")

    # Load check-in data
    try:
        with open('checkins.json', 'r') as file:
            checkin_data = json.load(file)
    except FileNotFoundError:
        checkin_data = {}
    except json.JSONDecodeError:
        checkin_data = {}


# Helper function to state timestamp for print lines
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
    
    print("Registered Commands:", [command.name for command in bot.tree.get_commands()])
    
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

    for guild_id in checkin_data:
        # Ensure the guild has the necessary structure
        guild_data = checkin_data[guild_id]
        if "current-month" not in guild_data:
            guild_data["current-month"] = {}
        if "monthly_history" not in guild_data:
            guild_data["monthly_history"] = {}

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
@bot.tree.command(name='checkin')
async def checkin(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    nickname = interaction.user.display_name
    current_time = datetime.datetime.now()
    current_month = get_current_month()

    # Initialize guild data if it doesn't exist
    if guild_id not in checkin_data:
        checkin_data[guild_id] = {
            "current-month": {},
            "monthly_history": {}
        }

    # Initialize current month data if it doesn't exist
    if current_month not in checkin_data[guild_id]["current-month"]:
        checkin_data[guild_id]["current-month"][current_month] = {}

    # Initialize user data if it doesn't exist
    if user_id not in checkin_data[guild_id]["current-month"][current_month]:
        checkin_data[guild_id]["current-month"][current_month][user_id] = {
            "nickname": nickname,
            "checkins": 0,
            "last_checkin": ""
        }

    # Get user data
    user_data = checkin_data[guild_id]["current-month"][current_month][user_id]

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

# -----------------------------------
#           Rankings           
# -----------------------------------
@bot.tree.command(name='prev_ranking')
async def prev_rankings(interaction: discord.Interaction):
@bot.tree.command(name='prev_ranking')
async def prev_rankings(interaction: discord.Interaction):
    print_with_timestamp("Previous rankings function is called")
    guild_id = str(interaction.guild.id)
    previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")
    current_month = get_current_month()

    if guild_id not in checkin_data or "current-month" not in checkin_data[guild_id] or current_month not in checkin_data[guild_id]["current-month"]:
        
        await interaction.respongithse.send_message(f"No check-ins for this server yet!")
        return
    elif guild_id in checkin_data and "monthly_history" in checkin_data and previous_month in checkin_data["monthly_history"]:
        await interaction.response.send_message(f"No data available for {previous_month}!")
        return

    # Get rankings for the current month
    rankings = sorted(
        [
            (user_id, data["checkins"], data["nickname"])
            for user_id, data in checkin_data[guild_id]["current-month"][current_month].items()
        ],
        key=lambda x: x[1],
        reverse=True
    )

    top_rankings = rankings[:min(10, len(rankings))]

    if top_rankings:
        leaderboard = "\n".join(
            [
                f"{'🥇' if index == 0 else '🥈' if index == 1 else '🥉' if index == 2 else f'{index + 1}. '} {checkin_data[user_id]['nickname']}: {checkins} check-ins"
                for index, (user_id, checkins) in enumerate(top_rankings)
            ]
        )
        await interaction.response.send_message(f"## Previous Month's Check-In Leaderboard ({previous_month})\n{leaderboard}")
    else:
        await interaction.response.send_message(f"No check-ins for {previous_month}!")
    

@bot.tree.command(name='winners')
async def print_winners(interaction: discord.Interaction):
    print_with_timestamp("Print winners function is called")
    previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

    if "monthly_history" in checkin_data and previous_month in checkin_data["monthly_history"]:
        rankings = sorted(
            checkin_data["monthly_history"][previous_month].items(),
            key=lambda x: x[1],
            reverse=True
        )

        filtered_rankings = []
        for user_id, checkins in rankings:
            member = interaction.guild.get_member(int(user_id))
            member = interaction.guild.get_member(int(user_id))
            if member and not any(role.name == "Admin" for role in member.roles):
                filtered_rankings.append((user_id, checkins, checkin_data[user_id]['nickname']))

        top_rankings = []
        current_rank = 1
        last_checkins = None
        places_collected = 0

        for i, (user_id, checkins, nickname) in enumerate(filtered_rankings):
            if last_checkins is None or checkins != last_checkins:
                current_rank = places_collected + 1

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
            await interaction.response.send_message(f"## Previous Month({previous_month})'s Top 3 Check-In Winners (excluding Admins)\n{leaderboard}")
            await interaction.response.send_message(f"## Previous Month({previous_month})'s Top 3 Check-In Winners (excluding Admins)\n{leaderboard}")
        else:
            await interaction.response.send_message(f"No eligible winners for {previous_month}!")
            await interaction.response.send_message(f"No eligible winners for {previous_month}!")
    else:
        await interaction.response.send_message(f"No data available for {previous_month}!")
        await interaction.response.send_message(f"No data available for {previous_month}!")

@bot.tree.command(name='ranking')
async def rankings(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)  # Get server ID
    current_month = get_current_month()

    if guild_id not in checkin_data or not checkin_data[guild_id]:
        await interaction.response.send_message(f"No check-ins for this server yet!")
        return

    # Sort rankings for the current guild
    rankings = sorted(
        [
            (user_id, data["checkins"], data["nickname"]) for user_id, data in checkin_data[guild_id].items()
            if data.get("month") == current_month and data["checkins"] > 0
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
        await interaction.response.send_message(f"## Current Month's Check-In Leaderboard ({current_month})\n{leaderboard}")
        await interaction.response.send_message(f"## Current Month's Check-In Leaderboard ({current_month})\n{leaderboard}")
    else:
        await interaction.response.send_message(f"No check-ins for this month yet!")


@bot.tree.command(name='hello')
async def prev_rankings(interaction: discord.Interaction):
    print_with_timestamp("Current rankings function is called")
    await interaction.response.send_message(f"Hydration is key 💧")
        await interaction.response.send_message(f"No check-ins for this month yet!")


@bot.tree.command(name='hello')
async def prev_rankings(interaction: discord.Interaction):
    print_with_timestamp("Current rankings function is called")
    await interaction.response.send_message(f"Hydration is key 💧")

# Run the program
bot.run(TOKEN)