import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import asyncio
from pathlib import Path
import json

from keep_alive import keep_alive

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('yapjail.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('yapjail')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    logger.error("❌ No DISCORD_TOKEN found in .env file")
    raise ValueError("No DISCORD_TOKEN found in .env file")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'✅ {bot.user} has connected to Discord!')
    logger.info(f'📊 Bot is in {len(bot.guilds)} guilds')
    
    # Load cogs
    try:
        await bot.load_extension('cogs.yapjail')
        logger.info('✅ YapJail cog loaded successfully!')
    except Exception as e:
        logger.error(f'❌ Failed to load YapJail cog: {e}')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} command(s)')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')
    
    # Log active jails
    try:
        with open('data/jailed_users.json', 'r') as f:
            data = json.load(f)
            if data:
                logger.info(f'🔒 {len(data)} users currently jailed')
    except:
        pass

@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f'Error in {event}: {args[0] if args else "Unknown"}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    logger.error(f'Command error: {error}')

# Run the bot
if __name__ == '__main__':
    try:
        logger.info("Starting YapJail bot...")
        keep_alive()
        bot.run(TOKEN)
    except KeyboardInterrupt:
        logger.info('Bot stopped by user')
    except Exception as e:
        logger.error(f'Bot crashed: {e}')