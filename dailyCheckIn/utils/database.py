import datetime
import os
import asyncio
import shutil
import aiomysql
from dotenv import load_dotenv
from utils.helpers import print_with_timestamp

load_dotenv()

DB_HOST = os.getenv("host")
DB_PORT = int(os.getenv("port", 3306))
DB_USER = os.getenv("username")
DB_PASS = os.getenv("password")
DB_NAME = os.getenv("database")
DB_SSL = os.getenv("sslmode")

db_pool = None

# Connection
async def init_db_pool():
    global db_pool
    db_pool = await aiomysql.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        autocommit=True
    )
    print_with_timestamp("Connected to MySQL database.")

# Setup
async def setup_database():
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS checkins (
                    guild_id VARCHAR(32),
                    user_id VARCHAR(32),
                    nickname VARCHAR(100),
                    checkin_date DATE,
                    PRIMARY KEY (guild_id, user_id, checkin_date)
                )
            ''')
            print_with_timestamp("✅ Table checkins ensured.")

# Backup
def backup_database():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"checkins_backup_{timestamp}.db"
    shutil.copyfile("checkins.db", backup_filename)
    print_with_timestamp(f"Database backed up as {backup_filename}")

# Auto backup
async def auto_backup_loop():
    while True:
        await asyncio.sleep(86400)  # wait 24 hours
        backup_database()
        
# Checkins
async def add_checkin(guild_id, user_id, nickname, checkin_date):
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute('''
                    INSERT IGNORE INTO checkins (guild_id, user_id, nickname, checkin_date)
                    VALUES (%s, %s, %s, %s)
                ''', (guild_id, user_id, nickname, checkin_date))
                return True
            except Exception as e:
                print_with_timestamp(f"❌ DB Insert Failed: {e}")
                return False

# Monthly and Total Counts
async def count_user_checkins(guild_id, user_id, month_prefix):
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Monthly count
            await cursor.execute('''
                SELECT COUNT(*) FROM checkins
                WHERE guild_id = %s AND user_id = %s AND checkin_date LIKE %s
            ''', (guild_id, user_id, f"{month_prefix}%"))
            monthly = (await cursor.fetchone())[0]

            # Total count
            await cursor.execute('''
                SELECT COUNT(*) FROM checkins
                WHERE guild_id = %s AND user_id = %s
            ''', (guild_id, user_id))
            total = (await cursor.fetchone())[0]

    return monthly, total

# Monthly checkin ranking
async def get_monthly_checkins(guild_id, month_prefix):
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute('''
                SELECT user_id, nickname, COUNT(*) AS checkins
                FROM checkins
                WHERE guild_id = %s AND checkin_date LIKE %s
                GROUP BY user_id, nickname
                ORDER BY checkins DESC
            ''', (guild_id, f"{month_prefix}%"))
            return await cursor.fetchall()

async def manual_add_checkin(guild_id, user_id, nickname, checkin_date):
    await add_checkin(guild_id, user_id, nickname, checkin_date)
