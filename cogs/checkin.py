from discord.ext import commands
from discord import app_commands, Interaction
import datetime
from utils.helpers import get_current_month, log_command_usage
from utils.database import db

class CheckIn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checkin", description="Check in for the day.")
    async def checkin(self, interaction: Interaction):
        log_command_usage(interaction, "checkin")

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        nickname = interaction.user.display_name
        current_time = datetime.datetime.now()
        current_date = current_time.strftime("%Y-%m-%d")

        success = await db.add_checkin(guild_id, user_id, nickname, current_date)

        # Get stats regardless of whether it was a duplicate
        current_month = get_current_month()
        monthly_count, total_count = await db.count_user_checkins(guild_id, user_id, current_month)
        
        if not success:
            # To the discord server
            await interaction.response.send_message(f'{interaction.user.mention}, you have already checked in today!', ephemeral=True)
        else:
            # To the discord server
            await interaction.response.send_message(
                f'{interaction.user.mention} chcked in! {monthly_count} time(s) this month · {total_count} time(s) in total'
            )
            
async def setup(bot):
    await bot.add_cog(CheckIn(bot))
