import discord
from discord.ext import commands
import os
import asyncio

TOKEN = 'xxxx'  # Replace with your token

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot connected as {bot.user}')

async def main():
    async with bot:
        # Load cogs safely
        for file in os.listdir('./cogs'):
            if file.endswith('.py') and file != '__init__.py':
                await bot.load_extension(f'cogs.{file[:-3]}')
        await bot.start(TOKEN)

# Run the async main loop
asyncio.run(main())
