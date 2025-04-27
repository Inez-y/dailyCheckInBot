from discord.ext import commands
from discord import Interaction, app_commands
from utils.data_handler import load_checkin_data
from utils.helpers import get_current_month, log_command_failure
from utils.helpers import log_command_usage


class Rankings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.checkin_data = load_checkin_data()

    @app_commands.command(name='ranking', description="View the current month's leaderboard.")
    async def rankings(self, interaction: Interaction):
        log_command_usage(interaction, "ranking")

        guild_id = str(interaction.guild.id)
        current_month = get_current_month()

        if guild_id not in self.checkin_data or current_month not in self.checkin_data[guild_id]["current-month"]:
            await interaction.response.send_message("No check-ins for this month yet!")
            log_command_failure(interaction, "ranking", "No check-ins found for this month.")
            return

        rankings = sorted(
            [(user_id, data["checkins"], data["nickname"]) for user_id, data in self.checkin_data[guild_id]["current-month"][current_month].items()],
            key=lambda x: x[1],
            reverse=True
        )

        leaderboard = "\n".join(
            [f"{index+1}. {nickname}: {checkins} check-ins" for index, (_, checkins, nickname) in enumerate(rankings)]
        )

        await interaction.response.send_message(f"## Current Month's Leaderboard ({current_month})\n{leaderboard}")

    # async def rankings(self, ctx):
    #     guild_id = str(ctx.guild.id)
    #     current_month = get_current_month()
        
        

    #     if guild_id not in self.checkin_data or current_month not in self.checkin_data[guild_id]["current-month"]:
    #         await ctx.send("No check-ins for this month yet!")
    #         return

    #     rankings = sorted(
    #         [(user_id, data["checkins"], data["nickname"]) for user_id, data in self.checkin_data[guild_id]["current-month"][current_month].items()],
    #         key=lambda x: x[1],
    #         reverse=True
    #     )

    #     leaderboard = "\n".join(
    #         [f"{index+1}. {nickname}: {checkins} check-ins" for index, (_, checkins, nickname) in enumerate(rankings)]
    #     )

    #     await ctx.send(f"## Current Month's Leaderboard ({current_month})\n{leaderboard}")

async def setup(bot):
    await bot.add_cog(Rankings(bot))
