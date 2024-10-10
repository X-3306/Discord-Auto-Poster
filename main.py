import discord
from discord.ext import commands, tasks
import datetime
import os
from dotenv import load_dotenv
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Constants
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
FILES_FOLDER = os.getenv('FILES_FOLDER')
USER_ID = int(os.getenv('USER_ID'))

# List of files to send
files_to_send = []

@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')
    await load_files()
    check_time.start()

async def load_files():
    global files_to_send
    files_to_send = [f for f in os.listdir(FILES_FOLDER) if f.endswith(('.txt', '.pdf'))]
    logging.info(f"Loaded {len(files_to_send)} files.")

@tasks.loop(minutes=1)
async def check_time():
    now = datetime.datetime.now()
    logging.info(f"Current time: {now.strftime('%H:%M')}")
    
    if now.hour == 7 and now.minute == 45:
        await send_daily_article()
    elif now.hour == 15 and now.minute == 30:
        await send_daily_article()
    elif now.hour == 18 and now.minute == 30:
        await send_daily_article()
    elif now.hour == 20 and now.minute == 00:
        await send_daily_article()

async def send_daily_article():
    if files_to_send:
        file_name = files_to_send.pop(0)
        file_path = os.path.join(FILES_FOLDER, file_name)

        try:
            channel = bot.get_channel(CHANNEL_ID)
            if channel is None:
                raise ValueError(f"Channel with ID {CHANNEL_ID} not found.")

            if file_name.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                await channel.send(f"**TITLE: {first_line}**")
                await channel.send(file=discord.File(file_path))
            elif file_name.endswith('.pdf'):
                await channel.send(f"**New PDF book: {file_name}**")
                await channel.send(file=discord.File(file_path))

            logging.info(f"Sent article: {file_name}")
        except Exception as e:
            logging.error(f"Error sending file {file_name}: {e}")
            await send_error_to_user(f"An error occurred while sending the article: {e}")
    else:
        await send_error_to_user("Resources exhausted. Please add new files.")
        await load_files()


async def send_error_to_user(message):
    user = bot.get_user(USER_ID)
    if user is None:
        logging.error(f"User with ID {USER_ID} not found.")
    else:
        try:
            await user.send(message)
        except discord.errors.Forbidden:
            logging.error(f"Unable to send a message to the user {USER_ID}.  Missing permissions.")
        except Exception as e:
            logging.error(f"Error sending message to user: {e}")

@bot.event
async def on_error(event, *args, **kwargs):
    logging.error(f"Unhandled error in event {event}", exc_info=True)


bot.run(os.getenv('TOKEN'))