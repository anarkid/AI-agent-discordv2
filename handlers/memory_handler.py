import os
import json

class MemoryHandler:
    def __init__(self, memory_dir="memories"):
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)

    def load(self, guild_id=None, user_id=None):
        memory_file = self._get_path(guild_id, user_id)
        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
                return json.load(f)
        return {"servers": {}}

    def save(self, memory_data, guild_id=None, user_id=None):
        memory_file = self._get_path(guild_id, user_id)
        with open(memory_file, "w") as f:
            json.dump(memory_data, f, indent=4)

    def _get_path(self, guild_id, user_id):
        if guild_id:
            return os.path.join(self.memory_dir, f"guild_{guild_id}.json")
        elif user_id:
            return os.path.join(self.memory_dir, f"user_{user_id}.json")
        raise ValueError("Either guild_id or user_id must be provided.")
