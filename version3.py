import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, ChatAdminRequiredError, ChatWriteForbiddenError
from dotenv import load_dotenv
import os
import signal
import sys

# Load environment variables from .env file
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
phone_number = os.getenv("PHONE_NUMBER")
reporting_telegram_id = int(os.getenv("REPORTING_TELEGRAM_ID"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)

# Create the client with a session file
client = TelegramClient('promo_name', api_id, api_hash)

# List of group chat IDs and their message intervals (in seconds)
groups_config = {
    -1001861632038: 5,
    -1002354039220: 5,
    -1002230285670: 10,
    -1001649611747: 10,
}

# Custom message to send
message_to_send = """\n\n**BALOON AKKA & NILA NAMBIAR😎**\n\n**🎥 PREMIUM COLLECTION UPLOADED FOR FREE❣️**\n\n[https://t.me/+uEjLYysyAqc5Y2E1]\n**open ah pesura boys and girls mattum vaanga**\n**🎥 FREE DEMO SHOW AND FREE TAMIL VIDEOS❣️**\n\n[https://t.me/romanticulagam]"""

# Start time of the bot
start_time = None  # Set to None initially

# Function to send messages
async def send_message(group_id):
    try:
        logging.info(f"Sending message to group {group_id}")
        await client.send_message(group_id, message_to_send)
        logging.info(f"Message successfully sent to group {group_id}")
    except FloodWaitError as e:
        logging.warning(f"Flood wait for {e.seconds} seconds while sending to group {group_id}. Retrying...")
        await asyncio.sleep(e.seconds)
        await send_message(group_id)
    except ChatAdminRequiredError:
        logging.error(f"Bot lacks admin rights in group {group_id}. Skipping...")
    except ChatWriteForbiddenError:
        logging.error(f"Cannot send messages to group {group_id}. Skipping...")
    except Exception as e:
        logging.error(f"Unexpected error while sending to group {group_id}: {e}")

# Scheduler function
async def schedule_messages():
    tasks = []
    for group_id, interval in groups_config.items():
        tasks.append(schedule_group_messages(group_id, interval))
    tasks.append(report_runtime())  # Add the runtime reporting task
    await asyncio.gather(*tasks)

async def schedule_group_messages(group_id, interval):
    while True:
        await send_message(group_id)
        logging.info(f"Waiting {interval} seconds before sending to group {group_id} again.")
        await asyncio.sleep(interval)

# Function to report total runtime via Telegram
async def report_runtime():
    global start_time
    if start_time is None:
        start_time = datetime.now()  # Initialize start time when the bot starts
    while True:
        current_time = datetime.now()
        elapsed_time = current_time - start_time
        runtime_message = f"Bot has been running for {str(elapsed_time).split('.')[0]} (HH:MM:SS)."
        logging.info(f"Preparing to send runtime report: {runtime_message}")

        try:
            await client.send_message(reporting_telegram_id, runtime_message)
            logging.info(f"Runtime report sent successfully to {reporting_telegram_id}")
        except Exception as e:
            logging.error(f"Error while sending runtime report via Telegram: {e}")

        await asyncio.sleep(3600)  # Send report every hour

# Command handler
@client.on(events.NewMessage)
async def command_handler(event):
    if event.text.lower() == 'start':
        await event.respond("Hello! I'm running and sending messages.")
        logging.info("Received 'start' command.")
    elif event.text.lower() == 'status':
        elapsed_time = datetime.now() - start_time if start_time else datetime.now()
        status_message = f"Bot is operational and has been running for {str(elapsed_time).split('.')[0]} (HH:MM:SS)."
        await event.respond(status_message)
        logging.info("Received 'status' command.")
    elif event.text.lower() == 'stop':
        elapsed_time = datetime.now() - start_time if start_time else datetime.now()
        stop_message = f"Bot stopped after running for {str(elapsed_time).split('.')[0]} (HH:MM:SS)."
        await client.send_message(reporting_telegram_id, stop_message)
        logging.info(f"Sent stop report: {stop_message}")
        logging.info("Disconnecting the bot.")
        await client.disconnect()
        sys.exit(0)  # Exit the script gracefully

async def main():
    global start_time
    # Authenticate and start the client
    await client.start(phone_number)
    me = await client.get_me()
    logging.info(f"Logged in as {me.username or me.phone}")
    start_time = datetime.now()  # Set start time when the bot starts
    await schedule_messages()

def shutdown_handler(signal, frame):
    logging.info("Shutting down gracefully...")
    asyncio.run(client.disconnect())
    sys.exit(0)

# Run the script
if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
