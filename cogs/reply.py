from discord.ext import commands
import asyncio
import re
import logging

from handlers.filehandler import FileHandler
from handlers.personalityhandler import PersonalityHandler
from handlers.memory_handler import MemoryHandler
from handlers.prompt_builder import PromptBuilder
from handlers.response_handler import ResponseHandler

logger = logging.getLogger("reply")

class ReplyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.file_handler = FileHandler()
        self.personality_handler = PersonalityHandler()
        self.memory_handler = MemoryHandler()
        self.response_handler = ResponseHandler()

    @commands.command(help='Ask the bot something or upload a file to get insights!')
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reply(self, ctx, *, question: str = None):
        is_dm = ctx.guild is None
        guild_id = str(ctx.guild.id) if not is_dm else None
        user_id = str(ctx.author.id) if is_dm else None
        target_id = guild_id if guild_id else f"user_{ctx.author.id}"
        channel_id = str(ctx.channel.id)

        # Load memory from cache or disk
        memory = self.memory_handler.load(guild_id=guild_id, user_id=user_id)
        if target_id not in memory['servers']:
            memory['servers'][target_id] = {}

        # Gather combined historical context
        combined_context = ""
        server_memory = memory['servers'].get(target_id, {})
        for ch_id, conversations in server_memory.items():
            if ch_id == "personality":
                continue
            for convo in reversed(conversations[-10:]):
                if len(convo.get('user', '')) < 5 and len(convo.get('bot', '')) < 5:
                    continue
                file_part = f"\n[Related File Content]\n{convo['file_context']}" if 'file_context' in convo else ""
                combined_context += f"User: {convo['user']}\nBot: {convo['bot']}{file_part}\n\n"

        # Gather recent messages (limited to last 10 to improve speed)
        recent_msgs = []
        if not is_dm:
            async for msg in ctx.channel.history(limit=10):  # Reduced from 20 to 10
                if msg.author.bot:
                    continue
                content = msg.content.strip()
                if len(content) < 5 or content.startswith(('!', '/')):
                    continue
                recent_msgs.append(f"{msg.author.name}: {content}")
        recent_context = "\n".join(recent_msgs)

        # Process file attachments
        file_context = await self.file_handler.process_attachments(ctx.message.attachments)
        if ctx.message.attachments and not file_context:
            await ctx.send("📎 I saw the file but couldn’t read anything useful from it. Try a different format?")

        if not question and not file_context:
            await ctx.send("❗ Please ask a question or upload a file.")
            return

        # Retrieve and validate personality
        selected_personality = self.personality_handler.get_personality(guild_id=guild_id, user_id=user_id)
        if self.personality_handler.is_valid_personality(selected_personality):
            instruction = self.personality_handler.AVAILABLE_PERSONALITIES[selected_personality.lower()]
        else:
            instruction = self.personality_handler.AVAILABLE_PERSONALITIES["wholesome"]
            await ctx.send(f"⚠️ The personality `{selected_personality}` was not found. Falling back to `wholesome`.")

        # Use fallback text if no question provided
        question = question or "(No specific question provided. Summarize or interpret the attached document.)"

        # Optional: Skip model call if last user message was identical
        previous_convos = memory['servers'][target_id].get(channel_id, [])
        if previous_convos:
            last_entry = previous_convos[-1]
            if last_entry.get("user", "").strip() == question.strip():
                await ctx.send(last_entry["bot"])
                return

        # Truncate file context before injecting into prompt
        if file_context:
            file_context = self.truncate_file_context(file_context)

        # Build final prompt
        prompt = PromptBuilder.build(
            instruction=instruction,
            combined_context=combined_context,
            recent_context=recent_context,
            file_context=file_context,
            question=question
        )

        # Send placeholder message while thinking
        thinking = await ctx.send("🧠 Thinking...")
        try:
            reply = await asyncio.wait_for(self.response_handler.generate(prompt), timeout=60)
        except asyncio.TimeoutError:
            await thinking.edit(content="⏱️ The model took too long to respond.")
            return
        except Exception as e:
            logger.error(f"Error generating model reply: {e}")
            await thinking.edit(content="⚠️ Something went wrong while generating the response.")
            return

        await thinking.delete()

        # Clean and format the response
        cleaned_reply = self.clean_response(reply).replace('\\n', '\n')
        cleaned_reply = self.fix_links(cleaned_reply)

        # Save conversation to memory
        new_entry = {"user": question, "bot": cleaned_reply}
        if file_context:
            new_entry["file_context"] = file_context
        if channel_id not in memory['servers'][target_id]:
            memory['servers'][target_id][channel_id] = []
        memory['servers'][target_id][channel_id].append(new_entry)
        self.memory_handler.save(memory, guild_id=guild_id, user_id=user_id)

        # Send full response in chunks
        await self.send_long_message(ctx, cleaned_reply)

    def clean_response(self, text):
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
        return re.sub(r"^(Bot:|AI:|Assistant:|Response:)\s*", "", text, flags=re.IGNORECASE)

    def fix_links(self, text):
        # Remove trailing punctuation from links
        text = re.sub(r'(\[[^\]]+\]\([^)]+\))([,\.])', r'\1', text)

        # Wrap raw URLs with <>
        def repl(match):
            url = match.group(0)
            return url if url.startswith('<') else f"<{url}>"

        pattern = re.compile(r'(?<!\]\()https?://[^\s<>()]+', re.IGNORECASE)
        return pattern.sub(repl, text)

    def truncate_file_context(self, file_content: str, max_length: int = 1000) -> str:
        if len(file_content) <= max_length:
            return file_content.strip()
        head = file_content[:int(max_length * 0.6)].strip()
        tail = file_content[-int(max_length * 0.3):].strip()
        return f"{head}\n...\n{tail}"

    async def send_long_message(self, ctx, message):
        MAX_LENGTH = 2000
        chunks = []
        start = 0
        while start < len(message):
            end = start + MAX_LENGTH
            if end < len(message):
                newline_pos = message.rfind('\n', start, end)
                if newline_pos != -1 and newline_pos > start:
                    end = newline_pos + 1
            chunks.append(message[start:end])
            start = end
        for chunk in chunks:
            await ctx.send(chunk)

    @reply.error
    async def reply_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ You’re going too fast! Try again in `{error.retry_after:.1f}` seconds.")
        else:
            logger.error(f"Unexpected error in !reply: {error}")
            await ctx.send("⚠️ Something went wrong while processing your request.")

async def setup(bot):
    await bot.add_cog(ReplyCommands(bot))
