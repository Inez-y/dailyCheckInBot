# Daily Check-In Discord Bot 

A Discord bot that lets server members **check in once per day**, tracks **monthly + total counts**, and shows **leaderboards**. Includes **admin tools** and a (planned) **monthly top-3 announcement**. This bot is designed for BCIT Fitnes Club.

## Features

* `**/checkin**` — users check in for the day (1 per day)
* Shows user stats:

  * check-ins current month
  * check-ins all time
* `**/ranking**` — current month leaderboard
* `**/prev_rank**` — previous month top 10
* `**/winners**` — previous month top 3 (medals)
* Admin-only:

  * `**/admin_add_checkin**` — manually add a check-in for a member
  * `**/admin_backup*`* — manual DB backup (see notes below)

## Commands

### User Commands

* `/checkin`
  Check in for today. If you already checked in today, you’ll be told privately.

* `/ranking`
  Shows the **current month** leaderboard.

* `/prev_rank`
  Shows the **previous month** leaderboard (top 10).

* `/winners`
  Shows the **previous month** top 3 with medals.

### Admin Commands (requires “Admin” role)

* `/admin_add_checkin member:@User`
  Adds a check-in entry for the selected user for today.

* `/admin_backup`
  Creates a backup file (see “Notes & Gotchas” — current code references a SQLite file name).

---

## Project Structure

```text
dailyCheckIn/
  bot.py
  config.py
  requirements.txt
  cogs/
    admin.py
    checkin.py
    rankings.py
    scheduler.py
  utils/
    database.py
    helpers.py

checkInBotKey/
  ca-certificate.crt
```

---

## Requirements

* Python **3.10+** recommended
* A Discord bot token (AWS)
* A MySQL database (this project uses **aiomysql**)
* A CA certificate file for DB SSL:

  * `checkInBotKey/ca-certificate.crt`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the `dailyCheckIn/` folder (same level as `bot.py`):

```env
DISCORD_TOKEN=your_discord_bot_token

# Database (MySQL)
host=your_db_host
port=25060
username=your_db_user
password=your_db_password
database=your_db_name

# Optional (for monthly announcement feature)
CHANNEL_ID=123456789012345678
```

### About SSL

The database connection expects a CA cert at:

```text
checkInBotKey/ca-certificate.crt
```

That path is used inside `utils/database.py`.

---

## Running the Bot

From inside the `dailyCheckIn/` folder:

```bash
python bot.py
```

On startup the bot will:

* connect to the database
* ensure the `checkins` table exists
* load the slash command cogs
* sync slash commands

---

## Discord Setup

### Bot Permissions / Intents

This bot enables:

* `message_content`
* `members`

In the Discord Developer Portal, ensure you enable **Server Members Intent** if required by your bot’s usage and server size.

### Admin Role

Admin commands require a Discord role literally named:

```text
Admin
```

Users must have that role to use admin commands.

---

## Database Schema

The bot ensures a table named `checkins` exists:

* `guild_id` (server ID)
* `user_id` (Discord user ID)
* `nickname` (display name at time of check-in)
* `checkin_date` (DATE)
* Primary key: `(guild_id, user_id, checkin_date)` to prevent duplicate daily check-ins.

---

## Notes & Gotchas (important)

A few things in the code are worth knowing if someone else is setting this up:

1. **Monthly announcement is not started yet**

   * `cogs/scheduler.py` defines the loop `monthly_top3_announcement(bot)`, but `bot.py` currently doesn’t start it.
   * To enable it, you typically create a background task in `on_ready()`:

     * `bot.loop.create_task(monthly_top3_announcement(bot))`

2. **`CHANNEL_ID` should be an integer**

   * In `scheduler.py` it’s currently read as a string:

     * `CHANNEL_ID = os.getenv('CHANNEL_ID')`
   * `bot.get_channel()` expects an `int`. Convert it:

     * `CHANNEL_ID = int(os.getenv("CHANNEL_ID"))`

3. **`scheduler.py` database call is missing `await`**

   * Your database methods are `async` (e.g. `get_monthly_checkins`), so calls should be awaited:

     * `rows = await db.get_monthly_checkins(...)`

4. **Backup commands reference a SQLite filename**

   * `admin_backup` and `Database.backup_database()` copy `checkins.db`, but your live storage is MySQL.
   * If you want backups for MySQL, you’ll want a `mysqldump` approach (or remove these backup calls).

If you want, I can provide a small patch that fixes the scheduler + backup mismatch cleanly.

---

## Customization Ideas

* Add streaks (consecutive days)
* Weekly leaderboard
* Auto-reset nicknames or store user tag + ID for stable naming
* Announce daily check-in reminders
* Separate leaderboards by roles / channels

