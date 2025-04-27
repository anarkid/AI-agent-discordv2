import discord
from discord.ext import commands
from discord.ui import Button, View
import os
import json
from utility.personalityhandler import PersonalityHandler

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.memory_file = "memory.json"
        self.handler = PersonalityHandler(memory_file=self.memory_file)

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return {"servers": {}}

    def save_memory(self, memory_data):
        with open(self.memory_file, "w") as f:
            json.dump(memory_data, f, indent=4)

    @commands.command(name='commands', help='List all available bot commands.')
    async def list_commands(self, ctx):
        commands_list = [
            "`!reply <message>` - Ask the bot or upload a PDF/DOCX/TXT/PPTX file.",
            "`!commands` - List all commands.",
            "`!forget` - Erase the bot's memory of this server.",
            "`!chooseTone` - Choose a personality for the bot to use.",
            "`!getTone` - Check the bot's current personality.",
        ]
        await ctx.send("**🤖 Available Commands:**\n" + "\n".join(commands_list))

    @commands.command(name='forget', help="Erase the bot's memory of this server, but keep personality settings.")
    async def clear_memory(self, ctx):
        memory = self.load_memory()
        target_id = str(ctx.guild.id) if ctx.guild else f"user_{ctx.author.id}"
        
        if target_id in memory["servers"]:
            personality = memory["servers"][target_id].get("personality", None)
            memory["servers"][target_id] = {"personality": personality} if personality else {}
            self.save_memory(memory)
            await ctx.send("🧹 Conversation memory erased. Personality settings remain unchanged.")
        else:
            await ctx.send("ℹ️ No memory found for this server.")

    @commands.command(name='getTone', help="Check the bot's current personality.")
    async def get_personality(self, ctx):
        target_id = str(ctx.guild.id) if ctx.guild else f"user_{ctx.author.id}"
        current_personality = self.handler.get_personality(target_id)
        await ctx.send(f"🎭 Current personality: **{current_personality}**")

    @commands.command(name='chooseTone', help="Choose the bot's personality.")
    async def choose_personality(self, ctx):
        personalities = self.handler.get_available_personalities()
        personality_keys = list(personalities.keys())

        # Pagination: show 5 personalities at a time
        items_per_page = 5
        total_pages = len(personality_keys) // items_per_page + (1 if len(personality_keys) % items_per_page != 0 else 0)

        # Show the first page
        page = 1
        view = await self.create_personality_buttons(personality_keys, page, total_pages)

        # Send the first message
        message = await ctx.send("🎭 **Choose a personality**:", view=view)

        # Wait for the user interaction (buttons press)
        await view.wait()

        # After timeout or completion, remove the buttons
        await message.edit(view=None)

    async def create_personality_buttons(self, personalities, page, total_pages):
        # Get the current page's personalities
        items_per_page = 5
        start = (page - 1) * items_per_page
        end = min(page * items_per_page, len(personalities))
        page_personalities = personalities[start:end]

        # Create buttons for each personality
        buttons = [
            Button(label=personality, custom_id=personality) for personality in page_personalities
        ]

        # Add navigation buttons
        view = View(timeout=60)  # Timeout after 60 seconds

        # Page navigation buttons
        if page > 1:
            prev_button = Button(label="⬅️ Previous", custom_id=f"prev_page_{page}")
            prev_button.callback = self.paginate_previous
            view.add_item(prev_button)

        for button in buttons:
            button.callback = self.set_personality_callback
            view.add_item(button)

        if page < total_pages:
            next_button = Button(label="➡️ Next", custom_id=f"next_page_{page}")
            next_button.callback = self.paginate_next
            view.add_item(next_button)

        return view

    async def set_personality_callback(self, interaction: discord.Interaction):
        personality = interaction.data["custom_id"]

        target_id = str(interaction.guild.id) if interaction.guild else f"user_{interaction.user.id}"
        self.handler.set_personality(target_id, personality)
        
        await interaction.response.send_message(f"🎭 Personality set to **{personality}**", ephemeral=True)

    async def paginate_previous(self, interaction: discord.Interaction):
        # Extract the current page from the custom_id
        page = int(interaction.data["custom_id"].split("_")[2]) - 1
        personality_keys = list(self.handler.get_available_personalities().keys())
        total_pages = len(personality_keys) // 5 + (1 if len(personality_keys) % 5 else 0)
        
        view = await self.create_personality_buttons(personality_keys, page, total_pages)
        await interaction.response.edit_message(view=view)

    async def paginate_next(self, interaction: discord.Interaction):
        # Extract the current page from the custom_id
        page = int(interaction.data["custom_id"].split("_")[2]) + 1
        personality_keys = list(self.handler.get_available_personalities().keys())
        total_pages = len(personality_keys) // 5 + (1 if len(personality_keys) % 5 else 0)
        
        view = await self.create_personality_buttons(personality_keys, page, total_pages)
        await interaction.response.edit_message(view=view)


async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))
