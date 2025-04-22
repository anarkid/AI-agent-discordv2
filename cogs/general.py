from discord.ext import commands
import os
import json
import time
from utility.personalityhandler import PersonalityHandler

MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"timestamp": time.time(), "servers": {}}

def save_memory(memory_data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory_data, f, indent=4)

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.handler = PersonalityHandler(memory_file=MEMORY_FILE)

    @commands.command(name='commands', help='List all available bot commands.')
    async def list_commands(self, ctx):
        commands_list = [
            "`!reply <message>` - Ask the bot or upload a PDF/DOCX file.",
            "`!commands` - List all commands.",
            "`!forget` - Erase the bot's memory of this server.",
            "`!setTone [style]` - Set the bot's personality style.",
            "`!listTone` - Show all available personalities."
        ]
        await ctx.send("**🤖 Available Commands:**\n" + "\n".join(commands_list))

    @commands.command(name='forget', help="Erase the bot's memory of this server, but keep personality settings.")
    async def clear_memory(self, ctx):
        memory = load_memory()
        guild_id = str(ctx.guild.id)
        
        if guild_id in memory["servers"]:
            # Preserve the personality setting by copying it before clearing the conversations
            personality = memory["servers"][guild_id].get("personality", None)

            # Clear all conversation history but keep personality
            memory["servers"][guild_id] = {"personality": personality} if personality else {}

            save_memory(memory)
            await ctx.send("🧹 Conversation memory erased. Personality settings remain unchanged.")
        else:
            await ctx.send("ℹ️ No memory found for this server.")

    @commands.command(name='setTone', help="Set the bot's personality. Usage: !setTone [style]")
    async def set_personality(self, ctx, *, style: str = None):
        if not style:
            available = ', '.join(self.handler.get_available_personalities().keys())
            await ctx.send(f"❗ Please specify a tone. Available: {available}")
            return

        if not self.handler.is_valid_personality(style):
            await ctx.send("❌ Invalid personality style. Use `!listTone` to view available options.")
            return

        self.handler.set_personality(ctx.guild.id, style)
        await ctx.send(f"🎭 Personality set to **{style}** for this server!")

    @commands.command(name='listTone', help="List all available personalities.")
    async def list_personalities(self, ctx):
        personalities = self.handler.get_available_personalities()
        desc = '\n'.join([f"**{name}**: {desc}" for name, desc in personalities.items()])
        await ctx.send(f"🎭 **Available Personalities:**\n{desc}")

async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))
