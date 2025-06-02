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

        # Load memory
        memory = self.memory_handler.load(guild_id=guild_id, user_id=user_id)
        if target_id not in memory['servers']:
            memory['servers'][target_id] = {}

        # Collect combined context from past interactions
        combined_context = ""
        for ch_id, conversations in memory['servers'][target_id].items():
            if ch_id == "personality":
                continue
            for convo in reversed(conversations[-10:]):
                if len(convo.get('user', '')) < 5 and len(convo.get('bot', '')) < 5:
                    continue
                file_part = f"\n[Related File Content]\n{convo['file_context']}" if 'file_context' in convo else ""
                combined_context += f"User: {convo['user']}\nBot: {convo['bot']}{file_part}\n\n"

        # Gather recent messages from this channel
        recent_msgs = []
        if not is_dm:
            async for msg in ctx.channel.history(limit=20):
                if msg.author.bot:
                    continue
                content = msg.content.strip()
                if not content or len(content) < 5:
                    continue
                if msg.content.startswith('!') or msg.content.startswith('/'):
                    continue
                recent_msgs.append(f"{msg.author.name}: {content}")
        recent_context = "\n".join(recent_msgs)

        # Handle file uploads
        file_context = await self.file_handler.process_attachments(ctx.message.attachments)
        if ctx.message.attachments and not file_context:
            await ctx.send("📎 I saw the file but couldn’t read anything useful from it. Try a different format?")
        elif file_context:
            file_context = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED_EMAIL]', file_context)
            file_context = re.sub(r'\b\d{10,}\b', '[REDACTED_NUMBER]', file_context)

        if not question and not file_context:
            await ctx.send("❗ Please ask a question or upload a file.")
            return

        # Retrieve and validate personality
        selected_personality = self.personality_handler.get_personality(guild_id=guild_id, user_id=user_id)
        if self.personality_handler.is_valid_personality(selected_personality):
            instruction = self.personality_handler.AVAILABLE_PERSONALITIES[selected_personality.lower()]
        else:
            instruction = self.personality_handler.AVAILABLE_PERSONALITIES["wholesome"]
            await ctx.send(
                f"⚠️ The personality `{selected_personality}` was not found. Falling back to `wholesome`."
            )

        # Build prompt
        question = question or "(No specific question provided. Summarize or interpret the attached document.)"
        prompt = PromptBuilder.build(
            instruction=instruction,
            combined_context=combined_context,
            recent_context=recent_context,
            file_context=file_context,
            question=question
        )

        # Generate model reply
        thinking = await ctx.send("🧠 Thinking...")
        try:
            reply = await asyncio.wait_for(self.response_handler.generate(prompt), timeout=60)
        except asyncio.TimeoutError:
            await thinking.edit(content="⏱️ The model took too long to respond.")
            return
        await thinking.delete()

        # Clean reply
        cleaned_reply = self.clean_response(reply)
        cleaned_reply = cleaned_reply.replace('\\n', '\n')

        # Fix link formatting for Discord
        cleaned_reply = self.fix_links(cleaned_reply)

        # Save to memory
        new_entry = {"user": question, "bot": cleaned_reply}
        if file_context:
            new_entry["file_context"] = self.truncate_file_context(file_context)
        if channel_id not in memory['servers'][target_id]:
            memory['servers'][target_id][channel_id] = []
        memory['servers'][target_id][channel_id].append(new_entry)
        self.memory_handler.save(memory, guild_id=guild_id, user_id=user_id)

        await self.send_long_message(ctx, cleaned_reply)

    def clean_response(self, text):
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
        return re.sub(r"^(Bot:|AI:|Assistant:|Response:)\s*", "", text, flags=re.IGNORECASE)
    
    def fix_links(self, text):
        # Remove trailing commas/periods immediately after markdown links
        text = re.sub(r'(\[[^\]]+\]\([^)]+\))([,\.])', r'\1', text)

        # Wrap raw URLs (not part of markdown links) with < >
        def repl(match):
            url = match.group(0)
            if url.startswith('<') and url.endswith('>'):
                return url
            return f"<{url}>"

        pattern = re.compile(r'(?<!\]\()https?://[^\s<>()]+', re.IGNORECASE)
        text = pattern.sub(repl, text)

        return text


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
