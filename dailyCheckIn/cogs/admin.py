import datetime
from discord.ext import commands
from discord import Interaction, app_commands

from utils.data_handler import load_checkin_data, save_checkin_data, ensure_guild_data
from utils.helpers import get_current_month, log_command_usage

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.checkin_data = load_checkin_data()

    # Ain't working now due to ctx - temp save
    @app_commands.command(name='admin_monthly_reset')
    @commands.has_role('Admin')
    async def trigger_monthly_reset(self, interaction: Interaction):
        log_command_usage(interaction, "admin_monthly_reset")
        current_month = get_current_month()
        previous_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")

        for guild_id in self.checkin_data:
            ensure_guild_data(guild_id, self.checkin_data)
            guild_data = self.checkin_data[guild_id]

            if current_month in guild_data["current-month"]:
                guild_data["monthly_history"][previous_month] = guild_data["current-month"][current_month]

            guild_data["current-month"] = {current_month: {}}

        save_checkin_data(self.checkin_data)
        await ctx.send("Monthly reset completed!")

async def setup(bot):
    await bot.add_cog(Admin(bot))
