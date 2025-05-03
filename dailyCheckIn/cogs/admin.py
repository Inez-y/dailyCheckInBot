from discord.ext import commands
from discord import Interaction, app_commands, Member
from utils.helpers import log_command_usage
from utils.database import manual_add_checkin
import datetime
import shutil
import datetime

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Manually add cheeckin for a user
    @app_commands.command(name='admin_add_checkin', description="Admin command to manually add a check-in for a user.")
    @app_commands.describe(member="The user you want to add a check-in for")
    @commands.has_role('Admin')
    async def admin_add_checkin(self, interaction: Interaction, member: Member):
        log_command_usage(interaction, "admin_add_checkin")
        
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)
        nickname = member.display_name
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        await manual_add_checkin(guild_id, user_id, nickname, current_date)

        await interaction.response.send_message(f"Added a manual check-in for {member.mention} on {current_date} for {guild_id} by {user_id}.")

    # Backup database file
    @app_commands.command(name='admin_backup', description="Backup the database manually (admin only)")
    @commands.has_role('Admin')
    async def admin_backup(self, interaction: Interaction):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"checkins_backup_{timestamp}.db"
        shutil.copyfile("checkins.db", backup_filename)

        await interaction.response.send_message(f"Backup created: `{backup_filename}` by ", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
