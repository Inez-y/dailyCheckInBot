import datetime
import pytz

# Timestamp for logs
def print_with_timestamp(message):
    server_timezone = pytz.timezone('US/Eastern')
    local_timezone = pytz.timezone('US/Pacific')
    server_time = datetime.datetime.now(server_timezone)
    local_time = server_time.astimezone(local_timezone)
    timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# Get current month
def get_current_month():
    return datetime.datetime.now().strftime("%Y-%m")

# Print with timestamp whenever commands called
def log_command_usage(interaction, command_name: str):
    user = interaction.user.display_name
    guild_id = str(interaction.guild.id)
    current_month = datetime.datetime.now().strftime("%Y-%m")

    print_with_timestamp(f"Command '{command_name}' used | Guild: {guild_id} | Month: {current_month} | User: {user}")

# Error
def log_command_failure(interaction, command_name: str, reason: str):
    user = interaction.user.display_name
    guild_id = str(interaction.guild.id)
    current_month = datetime.datetime.now().strftime("%Y-%m")

    print_with_timestamp(
        f"⚠️ Command '{command_name}' failed | Guild: {guild_id} | Month: {current_month} | User: {user} | Reason: {reason}"
    )