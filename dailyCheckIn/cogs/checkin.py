from discord.ext import commands
from discord import app_commands, Interaction
import datetime
from utils.helpers import log_command_usage
from utils.database import add_checkin

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

        success = add_checkin(guild_id, user_id, nickname, current_date)

        if not success:
            # To the discord server
            await interaction.response.send_message(f'{interaction.user.mention}, you have already checked in today!', ephemeral=True)
        else:
            # To the discord server
            await interaction.response.send_message(f'{interaction.user.mention}, check-in successful for today!')
            
async def setup(bot):
    await bot.add_cog(CheckIn(bot))
