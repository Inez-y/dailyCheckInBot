import datetime
import pytz

# Timestamp for logs(Helper function)
def print_with_timestamp(message):
    server_timezone = pytz.timezone('US/Eastern')
    local_timezone = pytz.timezone('US/Pacific')
    server_time = datetime.datetime.now(server_timezone)
    local_time = server_time.astimezone(local_timezone)
    timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# Get current month(Helper function)
def get_current_month():
    return datetime.datetime.now().strftime("%Y-%m")

def get_guild_id(interaction):
    return str(interaction.guild.id)

def get_user(interaction):
    return interaction.user.display_name

# Print with timestamp whenever commands called
def log_command_usage(interaction, command_name: str):
    print_with_timestamp(f"Command '{command_name}' used | Guild: {get_guild_id(interaction)} | Month: {get_current_month()} | User: {get_user(interaction)}")

# Error
def log_command_failure(interaction, command_name: str, reason: str):
    print_with_timestamp(
        f"⚠️ Command '{command_name}' failed | Guild: {get_guild_id(interaction)} | Month: {get_current_month()} | User: {get_user(interaction)} | Reason: {reason}"
    )