from discord.ext import commands
import json
import asyncio
import os
import re
import aiohttp
from utility.filehandler import FileHandler  # 📄 Handles file attachments
from utility.personalityhandler import PersonalityHandler  # 🎭 Personality module

class ReplyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.memory_file = "memory.json"
        self.file_handler = FileHandler()
        self.personality_handler = PersonalityHandler(memory_file=self.memory_file)

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return {"servers": {}}

    def save_memory(self, memory_data):
        with open(self.memory_file, "w") as f:
            json.dump(memory_data, f, indent=4)

    def clean_deepseek_reply(self, text):
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    @commands.command(help='Ask the bot something or upload a file to get insights!')
    @commands.cooldown(1, 10, commands.BucketType.user)  # ⏳ Cooldown to prevent spam
    async def reply(self, ctx, *, question: str = None):
        memory = self.load_memory()
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)

        if guild_id not in memory['servers']:
            memory['servers'][guild_id] = {}

        # 🧠 Combine previous bot-user exchanges
        combined_context = ""
        for ch_id, conversations in memory['servers'][guild_id].items():
            if ch_id == "personality":  # Skip the personality key
                continue
            for convo in conversations[-5:]:
                combined_context += f"User: {convo['user']}\nBot: {convo['bot']}\n\n"

        # 📜 Get recent messages in channel
        recent_msgs = []
        async for msg in ctx.channel.history(limit=10):
            if msg.author.bot:
                continue
            if msg.content.startswith('!reply'):
                content = msg.content.replace('!reply', '').strip()
                recent_msgs.append(f"User: {content}")
            else:
                recent_msgs.append(f"{msg.author.name}: {msg.content}")
        recent_context = "\n".join(recent_msgs)

        # 📄 Handle file attachments
        file_context = await self.file_handler.process_attachments(ctx.message.attachments)
        if ctx.message.attachments and not file_context:
            await ctx.send("📎 I saw the file but couldn’t read anything useful from it. Try a different format?")

        if not question and not file_context:
            await ctx.send("❗ Please ask a question or upload a file.")
            return

        # 🎭 Fetch personality for server
        personality_key = self.personality_handler.get_personality(guild_id)
        personality_instruction = self.personality_handler.AVAILABLE_PERSONALITIES.get(
            personality_key, self.personality_handler.AVAILABLE_PERSONALITIES["wholesome"]
        )

        question = question or "(No specific question provided. Summarize or interpret the attached document.)"
        context_text = f"{combined_context.strip()}\n{recent_context.strip()}\n\n{file_context.strip()}"
        formatted_prompt = (
            f"Here is the conversation context from this server:\n{context_text}\n\n"
            f"The user asked: \"{question}\"\n\n"
            f"Respond with this personality style:\n{personality_instruction}"
        )

        # 🧠 Send "thinking" message
        thinking_message = await ctx.send("🧠 Thinking...")

        # Start AI generation
        gen_task = asyncio.create_task(self.generate_response(formatted_prompt))

        # Wait for the response and delete the "thinking" message
        reply = await gen_task
        cleaned_reply = self.clean_deepseek_reply(reply)

        # Delete thinking message after response is ready
        await thinking_message.delete()

        # 💾 Save memory
        new_entry = {"user": question, "bot": cleaned_reply}
        if channel_id not in memory['servers'][guild_id]:
            memory['servers'][guild_id][channel_id] = []
        memory['servers'][guild_id][channel_id].append(new_entry)
        self.save_memory(memory)

        await self.send_long_message(ctx, cleaned_reply)

    async def generate_response(self, prompt):
        api_url = 'http://localhost:11434/api/generate' #change to target api
        model_name = "deepseek-v2:latest" #change to model used
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False #change to true if you want to
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload) as resp:
                    if resp.status != 200:
                        return f"❌ Error {resp.status}: Could not reach DeepSeek."
                    data = await resp.json()
                    return data.get("response", "🤖 No response from model.")
        except Exception as e:
            print(f"[DeepSeek Error] {e}")  # 🐞 Debug log
            return f"❌ Error contacting DeepSeek: {e}"

    async def send_long_message(self, ctx, message):
        for chunk in [message[i:i + 2000] for i in range(0, len(message), 2000)]:
            await ctx.send(chunk)

async def setup(bot):
    await bot.add_cog(ReplyCommands(bot))
