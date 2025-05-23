import datetime
from discord.ext import commands
from discord import Interaction, app_commands
from utils.helpers import get_current_month, log_command_failure
from utils.helpers import log_command_usage
from utils.database import db

class Rankings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Current month's ranking
    @app_commands.command(name='ranking', description="View the current month's leaderboard.")
    async def rankings(self, interaction: Interaction):
        log_command_usage(interaction, "ranking")

        guild_id = str(interaction.guild.id)
        current_month = get_current_month()

        rows = await db.get_monthly_checkins(guild_id, current_month)

        if not rows:
            await interaction.response.send_message("No check-ins for this month yet!")
            log_command_failure(interaction, "ranking", "No check-ins found for this month.")
            return

        leaderboard = "\n".join(
            [f"{index+1}. {row['nickname']}: {row['checkins']} check-ins" for index, row in enumerate(rows)]
        )

        # To the discord server
        await interaction.response.send_message(f"## Current Month's Leaderboard ({current_month})\n{leaderboard}")

    # Previous month's ranking
    @app_commands.command(name='prev_rank', description="View the previous month's top 10 leaderboard.")
    async def prev_rank(self, interaction: Interaction):
        log_command_usage(interaction, "prev_rank")

        guild_id = str(interaction.guild.id)

        # Calculate previous month
        now = datetime.datetime.now()
        first_day_of_current_month = now.replace(day=1)
        last_month_last_day = first_day_of_current_month - datetime.timedelta(days=1)
        previous_month = last_month_last_day.strftime("%Y-%m")

        rows = await db.get_monthly_checkins(guild_id, previous_month)

        if not rows:
            await interaction.response.send_message("No check-ins for the previous month!")
            log_command_failure(interaction, "prev_rank", "No check-ins found for previous month.")
            return

        # Only show top 10
        leaderboard = "\n".join(
            [f"{index+1}. {row['nickname']}: {row['checkins']} check-ins" for index, row in enumerate(rows[:10])]
        )

        await interaction.response.send_message(f"## Previous Month's Leaderboard ({previous_month})\n{leaderboard}")

    
    # top 3 winners from the previous month
    @app_commands.command(name='winners', description="View the previous month's top 3 leaderboard.")
    async def winners(self, interaction: Interaction):
        log_command_usage(interaction, "winners")

        guild_id = str(interaction.guild.id)

        # Calculate previous month
        now = datetime.datetime.now()
        first_day_of_current_month = now.replace(day=1)
        last_month_last_day = first_day_of_current_month - datetime.timedelta(days=1)
        previous_month = last_month_last_day.strftime("%Y-%m")

        rows = await db.get_monthly_checkins(guild_id, previous_month)

        if not rows:
            await interaction.response.send_message("No check-ins for the previous month!")
            log_command_failure(interaction, "prev_rank", "No check-ins found for previous month.")
            return
        
        # Admins are excluded
        rows = [r for r in rows if r['nickname'] != 'Admin']

        medals = ["🥇", "🥈", "🥉"]
        leaderboard = "\n".join(
            [f"{medals[index]} {row['nickname']}: {row['checkins']} check-ins" for index, row in enumerate(rows[:3])]
        )

        await interaction.response.send_message(
            f"🏆 **Previous Month's Top 3 Check-ins ({previous_month})**\n\n{leaderboard}"
        )

async def setup(bot):
    await bot.add_cog(Rankings(bot))
