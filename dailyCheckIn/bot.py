import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.helpers import print_with_timestamp
from utils.database import db

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot Setup
def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    return commands.Bot(command_prefix='/', intents=intents)

# Load Cogs (Modules)
bot = create_bot()
COGS = [
  "dailyCheckIn.cogs.checkin",
  "dailyCheckIn.cogs.rankings",
  "dailyCheckIn.cogs.admin",
]

# Functions
@bot.event
async def on_ready():
    await bot.tree.sync()
    print_with_timestamp(f'{bot.user.name} is online and slash commands synced!')

async def load_cogs():
    for cog in COGS:
        await bot.load_extension(cog)

async def main():
    await db.connect()
    await db.setup_database()
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())