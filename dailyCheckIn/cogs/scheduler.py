import asyncio
import datetime
import os
from utils.database import get_monthly_checkins
from utils.helpers import print_with_timestamp
from dotenv import load_dotenv

# General channel
load_dotenv()
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# For testing, add
# if now.minute % 1 == 0:  # every minute instead of 1st day 9AM

# For testing, remove temporarily
# # if now.day == 1 and now.hour == 9:
# if not already_announced:
#     await send_top3(bot)
#     already_announced = True


async def monthly_top3_announcement(bot):
    await bot.wait_until_ready()
    already_announced = False

    while not bot.is_closed():
        now = datetime.datetime.now()

        # Check if it's 1st day and after 9:00AM
        if now.day == 1 and now.hour == 9:
            if not already_announced:
                await send_top3(bot)
                already_announced = True
        else:
            already_announced = False  # Reset flag for next month

        await asyncio.sleep(60)  # check every minute

async def send_top3(bot):
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print_with_timestamp("⚠️ Warning: Channel not found!")
        return

    # Figure out previous month
    now = datetime.datetime.now()
    first_day_of_current_month = now.replace(day=1)
    last_month_last_day = first_day_of_current_month - datetime.timedelta(days=1)
    previous_month = last_month_last_day.strftime("%Y-%m")

    guild_id = str(channel.guild.id)

    rows = get_monthly_checkins(guild_id, previous_month)

    if not rows:
        await channel.send(f"❌ No check-ins for {previous_month}.")
        print_with_timestamp("❌ No previous month data found.")
        return

    # Only top 3
    top3 = rows[:3]

    if not top3:
        await channel.send(f"❌ No top 3 users available.")
        return

    # Make the announcement message
    medals = ["🥇", "🥈", "🥉"]
    message = f"🏆 **Top 3 Check-ins for {previous_month}** 🏆\n\n"

    for index, row in enumerate(top3):
        message += f"{medals[index]} {row['nickname']} — {row['checkins']} check-ins\n"

    await channel.send(message)
    print_with_timestamp(f"✅ Posted top 3 for {previous_month}.")

