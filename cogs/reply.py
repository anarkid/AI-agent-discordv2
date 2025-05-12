from discord.ext import commands
import json
import asyncio
import os
import re
import aiohttp
from utility.filehandler import FileHandler
from utility.personalityhandler import PersonalityHandler
from datetime import datetime

class ReplyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.memory_dir = "memories"
        os.makedirs(self.memory_dir, exist_ok=True)
        self.file_handler = FileHandler()
        self.personality_handler = PersonalityHandler(memory_dir=self.memory_dir)

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

    def clean_deepseek_reply(self, text):
        # Remove hidden tags like <think>...</think>
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
        
        # Remove leading AI-style prefixes (case-insensitive)
        cleaned = re.sub(r"^(Bot:|AI:|Assistant:|Response:)\s*", "", cleaned, flags=re.IGNORECASE)
        
        return cleaned

    def get_current_time(self):
        # Get current time in the format: "Monday, May 12, 2025 at 11:09 PM"
        return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    @commands.command(help='Ask the bot something or upload a file to get insights!')
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reply(self, ctx, *, question: str = None):
        is_dm = ctx.guild is None
        guild_id = str(ctx.guild.id) if not is_dm else None
        user_id = str(ctx.author.id) if is_dm else None
        target_id = str(ctx.guild.id) if ctx.guild else f"user_{ctx.author.id}"
        channel_id = str(ctx.channel.id)

        # Detect time-related questions and handle separately
        if question:
            if re.search(r"\b(what\s+time\s+is\s+it|current\s+time|time\s+now|what's\s+the\s+time|tell\s+me\s+the\s+time|time\??)\b", question.lower()):
                # Get the current time
                current_time = self.get_current_time()

                # Retrieve personality
                selected_personality = self.personality_handler.get_personality(guild_id=guild_id, user_id=user_id)

                # Check if the personality exists and retrieve instruction
                if self.personality_handler.is_valid_personality(selected_personality):
                    instruction = self.personality_handler.AVAILABLE_PERSONALITIES[selected_personality.lower()]
                else:
                    instruction = self.personality_handler.AVAILABLE_PERSONALITIES["wholesome"]

                # Add the current time to the AI prompt and let the AI handle the response
                formatted_prompt = (
                    f"[System Instruction]\n"
                    f"You are AI assistant with following personality style:\n"
                    f"{instruction}\n\n"
                    f"[User Question]\n"
                    f"The user has asked for the current time. Here is the time: **{current_time}**.\n\n"
                    f"[Expected Behavior]\n"
                    f"Respond clearly and thoroughly, considering the provided context and maintaining the defined personality style."
                )

                # Send the prompt to the AI model and retrieve the response
                thinking_message = await ctx.send("🧠 Thinking...")
                try:
                    reply = await asyncio.wait_for(self.generate_response(formatted_prompt), timeout=60)
                except asyncio.TimeoutError:
                    await thinking_message.edit(content="⏱️ The model took too long to respond. Please try again.")
                    return

                await thinking_message.delete()

                cleaned_reply = self.clean_deepseek_reply(reply)
                await ctx.send(cleaned_reply)
                return

        # Load memory and build refined combined context (last 10 relevant interactions)
        memory = self.load_memory(guild_id=guild_id, user_id=user_id)
        if target_id not in memory['servers']:
            memory['servers'][target_id] = {}

        combined_context = ""
        for ch_id, conversations in memory['servers'][target_id].items():
            if ch_id == "personality":
                continue
            for convo in reversed(conversations[-10:]):
                if len(convo.get('user', '')) < 5 and len(convo.get('bot', '')) < 5:
                    continue

                file_part = f"\n[Related File Content]\n{convo['file_context']}" if 'file_context' in convo else ""
                combined_context += f"User: {convo['user']}\nBot: {convo['bot']}{file_part}\n\n"

        recent_msgs = []
        if not is_dm:
            async for msg in ctx.channel.history(limit=20):
                if msg.author.bot:
                    continue
                content = msg.content.strip()
                if not content or len(content) < 5:
                    continue
                if msg.content.startswith('!reply'):
                    content = msg.content.replace('!reply', '').strip()
                recent_msgs.append(f"{msg.author.name}: {content}")
        recent_context = "\n".join(recent_msgs)

        # Handle any uploaded files
        file_context = await self.file_handler.process_attachments(ctx.message.attachments)
        if ctx.message.attachments and not file_context:
            await ctx.send("📎 I saw the file but couldn’t read anything useful from it. Try a different format?")

        if not question and not file_context:
            await ctx.send("❗ Please ask a question or upload a file.")
            return

        # Retrieve personality from user memory
        selected_personality = self.personality_handler.get_personality(guild_id=guild_id, user_id=user_id)

        # Check if the personality exists and retrieve instruction
        if self.personality_handler.is_valid_personality(selected_personality):
            instruction = self.personality_handler.AVAILABLE_PERSONALITIES[selected_personality.lower()]
        else:
            instruction = self.personality_handler.AVAILABLE_PERSONALITIES["wholesome"]
            await ctx.send(
                f"⚠️ The personality `{selected_personality}` was not found. Falling back to `wholesome`."
            )

        # Formulate the question prompt with the context and the personality style
        question = question or "(No specific question provided. Summarize or interpret the attached document.)"
        formatted_prompt = (
            f"[System Instruction]\n"
            f"You are AI assistant with following personality style:\n"
            f"{instruction}\n\n"

            f"[Conversation History]\n"
            f"{combined_context.strip() or 'No significant previous interactions.'}\n\n"

            f"[Recent Channel Messages]\n"
            f"{recent_context.strip() or 'No recent relevant messages.'}\n\n"

            f"[File Attachment Summary]\n"
            f"{file_context.strip() or 'No file uploaded.'}\n\n"

            f"[User Question]\n"
            f"{question.strip()}\n\n"

            f"[Expected Behavior]\n"
            f"Respond clearly and thoroughly, considering all the provided context and maintaining the defined personality style."
        )

        thinking_message = await ctx.send("🧠 Thinking...")
        try:
            reply = await asyncio.wait_for(self.generate_response(formatted_prompt), timeout=60)
        except asyncio.TimeoutError:
            await thinking_message.edit(content="⏱️ The model took too long to respond. Please try again.")
            return

        await thinking_message.delete()

        cleaned_reply = self.clean_deepseek_reply(reply)
        new_entry = {"user": question, "bot": cleaned_reply}

        if file_context:
            truncated_file_context = self.truncate_file_context(file_context)
            new_entry["file_context"] = truncated_file_context

        if channel_id not in memory['servers'][target_id]:
            memory['servers'][target_id][channel_id] = []
        memory['servers'][target_id][channel_id].append(new_entry)
        self.save_memory(memory, guild_id=guild_id, user_id=user_id)

        await self.send_long_message(ctx, cleaned_reply)

    async def generate_response(self, prompt):
        api_url = 'http://localhost:11434/api/generate'
        model_name = "deepseek-v2:latest"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload) as resp:
                    if resp.status != 200:
                        return f"❌ Error {resp.status}: Could not reach DeepSeek."
                    data = await resp.json()
                    return data.get("response", "🤖 No response from model.")
        except Exception as e:
            print(f"[DeepSeek Error] {e}")
            return f"❌ Error contacting DeepSeek: {e}"

    async def send_long_message(self, ctx, message):
        MAX_LENGTH = 2000
        words = message.split()
        chunks = []
        current_chunk = ""

        for word in words:
            if len(current_chunk) + len(word) + 1 > MAX_LENGTH:
                chunks.append(current_chunk)
                current_chunk = word
            else:
                current_chunk += (" " if current_chunk else "") + word

        if current_chunk:
            chunks.append(current_chunk)

        for chunk in chunks:
            await ctx.send(chunk)
    
    def truncate_file_context(self, file_content: str, max_length: int = 1000) -> str:
        if len(file_content) <= max_length:
            return file_content.strip()

        head = file_content[:int(max_length * 0.6)].strip()
        tail = file_content[-int(max_length * 0.3):].strip()
        return f"{head}\n...\n{tail}"

async def setup(bot):
    await bot.add_cog(ReplyCommands(bot))
