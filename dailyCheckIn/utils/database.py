import datetime
import os
import asyncio
import shutil
import aiomysql
import ssl
from dotenv import load_dotenv
from utils.helpers import print_with_timestamp

load_dotenv()

DB_HOST = os.getenv("host")
DB_PORT = int(os.getenv("port", 3306))
DB_USER = os.getenv("username")
DB_PASS = os.getenv("password")
DB_NAME = os.getenv("database")

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.pool = None
        return cls._instance

    async def connect(self):
        if self.pool is None:
            ssl_ctx = ssl.create_default_context()
            self.pool = await aiomysql.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASS,
                db=DB_NAME,
                autocommit=True,
                ssl=ssl_ctx
            )
            print_with_timestamp("Connected to MySQL database.")

    async def setup_database(self):
        async with self.pool.acquire() as conn:
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
                print_with_timestamp("Table checkins ensured.")

    def backup_database(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"checkins_backup_{timestamp}.db"
        shutil.copyfile("checkins.db", backup_filename)
        print_with_timestamp(f"Database backed up as {backup_filename}")

    async def auto_backup_loop(self):
        while True:
            await asyncio.sleep(86400)
            self.backup_database()

    async def add_checkin(self, guild_id, user_id, nickname, checkin_date):
        async with self.pool.acquire() as conn:
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

    async def count_user_checkins(self, guild_id, user_id, month_prefix):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('''
                    SELECT COUNT(*) FROM checkins
                    WHERE guild_id = %s AND user_id = %s AND checkin_date LIKE %s
                ''', (guild_id, user_id, f"{month_prefix}%"))
                monthly = (await cursor.fetchone())[0]

                await cursor.execute('''
                    SELECT COUNT(*) FROM checkins
                    WHERE guild_id = %s AND user_id = %s
                ''', (guild_id, user_id))
                total = (await cursor.fetchone())[0]

        return monthly, total

    async def get_monthly_checkins(self, guild_id, month_prefix):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute('''
                    SELECT user_id, nickname, COUNT(*) AS checkins
                    FROM checkins
                    WHERE guild_id = %s AND checkin_date LIKE %s
                    GROUP BY user_id, nickname
                    ORDER BY checkins DESC
                ''', (guild_id, f"{month_prefix}%"))
                return await cursor.fetchall()

    async def manual_add_checkin(self, guild_id, user_id, nickname, checkin_date):
        await self.add_checkin(guild_id, user_id, nickname, checkin_date)

# Singleton instance
db = Database()