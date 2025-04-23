import json
import os
from discord.ext import commands

class PersonalityHandler:
    AVAILABLE_PERSONALITIES = {
        "tsundere": "Aloof and irritated, but still care. Don't admit to being nice.",
        "professional": "Formal tone. Clear, efficient, and respectful. No fluff.",
        "cheerful": "Bubbly and excited. Use emojis and positive energy!",
        "sarcastic": "Dry, witty, and a bit mocking. Make sure it's playful, not rude.",
        "wholesome": "Gentle and kind. Use soft language. Supportive and warm.",
        "flirty": "Flirty, suggestive, and playful. Speak with innuendo but keep it light and cheeky.",
    }

    def __init__(self, memory_file="memory.json"):
        self.memory_file = memory_file

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return {"servers": {}}

    def save_memory(self, memory):
        with open(self.memory_file, "w") as f:
            json.dump(memory, f, indent=4)

    def get_personality(self, guild_id):
        memory = self.load_memory()
        return memory.get("servers", {}).get(str(guild_id), {}).get("personality", "wholesome")

    def set_personality(self, guild_id, personality):
        memory = self.load_memory()
        if str(guild_id) not in memory['servers']:
            memory['servers'][str(guild_id)] = {}
        memory['servers'][str(guild_id)]['personality'] = personality.lower()
        self.save_memory(memory)

    def is_valid_personality(self, personality):
        return personality.lower() in self.AVAILABLE_PERSONALITIES

    def get_available_personalities(self):
        return self.AVAILABLE_PERSONALITIES
