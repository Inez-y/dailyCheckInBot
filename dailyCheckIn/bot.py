import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.helpers import print_with_timestamp

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Load Cogs (Modules)
COGS = ["cogs.checkin", "cogs.rankings", "cogs.admin"]

@bot.event
async def on_ready():
    # Sync the slash commands
    await bot.tree.sync()
    print_with_timestamp(f'The bot has connected to Discord and slash commands synced!')

async def load_cogs():
    for cog in COGS:
        await bot.load_extension(cog)

# Start the bot
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())