import discord
from discord.ext import commands
from discord.ui import Button, View
import os
import json
from utility.personalityhandler import PersonalityHandler

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.memory_dir = "memories"
        os.makedirs(self.memory_dir, exist_ok=True)
        self.handler = PersonalityHandler(memory_dir=self.memory_dir)

    def load_memory(self, guild_id=None, user_id=None):
        if guild_id:
            memory_file = os.path.join(self.memory_dir, f"guild_{guild_id}.json")
        elif user_id:
            memory_file = os.path.join(self.memory_dir, f"user_{user_id}.json")
        else:
            return {"servers": {}}

        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
                return json.load(f)
        return {"servers": {}}

    def save_memory(self, memory_data, guild_id=None, user_id=None):
        if guild_id:
            memory_file = os.path.join(self.memory_dir, f"guild_{guild_id}.json")
        elif user_id:
            memory_file = os.path.join(self.memory_dir, f"user_{user_id}.json")
        else:
            return

        with open(memory_file, "w") as f:
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

    @commands.command(name='forget', help="Erase the bot's memory of this server or DM, but keep personality settings.")
    async def clear_memory(self, ctx):
        is_dm = ctx.guild is None
        guild_id = ctx.guild.id if not is_dm else None
        user_id = ctx.author.id if is_dm else None

        memory = self.load_memory(guild_id=guild_id, user_id=user_id)
        target_id = str(guild_id) if guild_id else f"user_{user_id}"

        if target_id in memory["servers"]:
            personality = memory["servers"][target_id].get("personality", None)
            memory["servers"][target_id] = {"personality": personality} if personality else {}
            self.save_memory(memory, guild_id=guild_id, user_id=user_id)
            await ctx.send("🧹 Conversation memory erased. Personality settings remain unchanged.")
        else:
            await ctx.send("ℹ️ No memory found to forget.")


    @commands.command(name='getTone', help="Check the bot's current personality.")
    async def get_personality(self, ctx):
        target_id = str(ctx.guild.id) if ctx.guild else f"user_{ctx.author.id}"
        current_personality = self.handler.get_personality(guild_id=ctx.guild.id if ctx.guild else None,
                                                           user_id=ctx.author.id if not ctx.guild else None)
        await ctx.send(f"🎭 Current personality: **{current_personality}**")

    @commands.command(name='chooseTone', help="Choose the bot's personality.")
    async def choose_personality(self, ctx):
        personalities = self.handler.get_available_personalities()
        personality_keys = list(personalities.keys())

        items_per_page = 5
        total_pages = len(personality_keys) // items_per_page + (1 if len(personality_keys) % items_per_page != 0 else 0)
        page = 1

        view = await self.create_personality_buttons(ctx, personality_keys, page, total_pages)
        message = await ctx.send("🎭 **Choose a personality**:", view=view)

        await view.wait()
        await message.edit(view=None)

    async def create_personality_buttons(self, ctx, personalities, page, total_pages):
        items_per_page = 5
        start = (page - 1) * items_per_page
        end = min(page * items_per_page, len(personalities))
        page_personalities = personalities[start:end]

        view = View(timeout=60)

        if page > 1:
            prev_button = Button(label="⬅️ Previous", custom_id=f"prev_page_{page}")
            async def prev_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("❌ You can't control this menu.", ephemeral=True)
                    return
                await interaction.response.edit_message(
                    view=await self.create_personality_buttons(ctx, personalities, page - 1, total_pages)
                )
            prev_button.callback = prev_callback
            view.add_item(prev_button)

        for personality in page_personalities:
            button = Button(label=personality, custom_id=personality)

            async def button_callback(interaction, p=personality):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("❌ You can't choose for someone else.", ephemeral=True)
                    return

                target_id = str(interaction.guild.id) if interaction.guild else f"user_{interaction.user.id}"
                self.handler.set_personality(guild_id=interaction.guild.id if interaction.guild else None,
                                             user_id=interaction.user.id if not interaction.guild else None,
                                             personality=p)

                memory = self.load_memory(guild_id=interaction.guild.id if interaction.guild else None,
                                          user_id=interaction.user.id if not interaction.guild else None)

                if target_id not in memory["servers"]:
                    memory["servers"][target_id] = {}
                memory["servers"][target_id]["personality"] = p
                self.save_memory(memory,
                                 guild_id=interaction.guild.id if interaction.guild else None,
                                 user_id=interaction.user.id if not interaction.guild else None)

                await interaction.response.send_message(f"🎭 Personality set to **{p}**", ephemeral=True)

            button.callback = button_callback
            view.add_item(button)

        if page < total_pages:
            next_button = Button(label="➡️ Next", custom_id=f"next_page_{page}")
            async def next_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("❌ You can't control this menu.", ephemeral=True)
                    return
                await interaction.response.edit_message(
                    view=await self.create_personality_buttons(ctx, personalities, page + 1, total_pages)
                )
            next_button.callback = next_callback
            view.add_item(next_button)

        return view

async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))
