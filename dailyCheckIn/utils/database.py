import asyncio
import datetime
import shutil
import sqlite3

from utils.helpers import print_with_timestamp

DB_FILE = "data/checkins.db"

# Connection
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    print_with_timestamp("Getting database connection...")
    return conn

# Setup
def setup_database():
    print_with_timestamp("Setting up database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            guild_id TEXT,
            user_id TEXT,
            nickname TEXT,
            checkin_date TEXT,
            PRIMARY KEY (guild_id, user_id, checkin_date)
        )
    ''')

    conn.commit()
    conn.close()

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
def add_checkin(guild_id, user_id, nickname, checkin_date):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO checkins (guild_id, user_id, nickname, checkin_date)
            VALUES (?, ?, ?, ?)
        ''', (guild_id, user_id, nickname, checkin_date))
        conn.commit()
        print_with_timestamp("Added to the database...")
    except sqlite3.IntegrityError:
        # Already checked in today
        return False
    finally:
        conn.close()
    
    return True

# Monthly checkin ranking
def get_monthly_checkins(guild_id, month_prefix):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, nickname, COUNT(*) as checkins
        FROM checkins
        WHERE guild_id = ? AND checkin_date LIKE ?
        GROUP BY user_id
        ORDER BY checkins DESC
    ''', (guild_id, f"{month_prefix}%"))

    rows = cursor.fetchall()
    conn.close()
    return rows

# Add a user manually for an admin
def manual_add_checkin(guild_id, user_id, nickname, checkin_date):
    conn = get_db_connection()
    cursor = conn.cursor()

    # INSERT OR IGNORE: if the check-in already exists, do nothing
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO checkins (guild_id, user_id, nickname, checkin_date)
            VALUES (?, ?, ?, ?)
        ''', (guild_id, user_id, nickname, checkin_date))
        conn.commit()
    finally:
        conn.close()

