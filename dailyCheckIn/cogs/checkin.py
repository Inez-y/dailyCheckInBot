from discord.ext import commands
from discord import app_commands, Interaction
import datetime
import threading
from utils.data_handler import load_checkin_data, save_checkin_data, ensure_guild_data
from utils.helpers import get_current_month, log_command_usage

class CheckIn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.checkin_data = load_checkin_data()

    @app_commands.command(name="checkin", description="Check in for the day.")
    async def checkin(self, interaction: Interaction):
        log_command_usage(interaction, "checkin")
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        nickname = interaction.user.display_name
        current_time = datetime.datetime.now()
        current_month = get_current_month()

        ensure_guild_data(guild_id, self.checkin_data)

        with threading.Lock():
            guild_data = self.checkin_data[guild_id]

            if current_month not in guild_data["current-month"]:
                guild_data["current-month"][current_month] = {}

            if user_id not in guild_data["current-month"][current_month]:
                guild_data["current-month"][current_month][user_id] = {
                    "nickname": nickname,
                    "checkins": 0,
                    "last_checkin": ""
                }

            user_data = guild_data["current-month"][current_month][user_id]

            if user_data["last_checkin"] == current_time.strftime("%Y-%m-%d"):
                await interaction.response.send_message(f'{interaction.user.mention}, you have already checked in today!', ephemeral=True)
                return

            user_data["checkins"] += 1
            user_data["last_checkin"] = current_time.strftime("%Y-%m-%d")
            user_data["nickname"] = nickname

        save_checkin_data(self.checkin_data)
        await interaction.response.send_message(f'{interaction.user.mention}, check-in successful! Total check-ins: {user_data["checkins"]}')

async def setup(bot):
    await bot.add_cog(CheckIn(bot))
