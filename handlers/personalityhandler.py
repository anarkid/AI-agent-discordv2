import json
import os

class PersonalityHandler:
    def __init__(self, memory_dir="memories"):
        self.memory_dir = memory_dir  # Directory where memory files will be stored
        os.makedirs(self.memory_dir, exist_ok=True)  # Ensure the directory exists
        self.AVAILABLE_PERSONALITIES = self.load_personalities()

    def load_personalities(self):
        """Load all personalities from the personalities folder."""
        all_personalities = {}

        # Directory where personality packs are stored
        personality_folder = "utility/personalities"
        
        # Load default personalities from a specific file (if any)
        with open(os.path.join(personality_folder, 'default.json')) as f:
            default_personalities = json.load(f)
            all_personalities.update(default_personalities)

        # Dynamically load all other JSON files in the personalities folder
        for filename in os.listdir(personality_folder):
            if filename.endswith(".json") and filename != "default.json":
                with open(os.path.join(personality_folder, filename)) as f:
                    personality_pack = json.load(f)
                    all_personalities.update(personality_pack)

        return all_personalities

    def get_available_personalities(self):
        """Return a dictionary of available personalities."""
        return self.AVAILABLE_PERSONALITIES

    def is_valid_personality(self, personality):
        """Check if the given personality is valid."""
        return personality.lower() in self.AVAILABLE_PERSONALITIES

    def set_personality(self, guild_id=None, user_id=None, personality=None):
        """Set the personality for a specific guild or user."""
        memory = self.load_memory(guild_id=guild_id, user_id=user_id)
        target_id = str(guild_id) if guild_id else f"user_{user_id}"
        
        if target_id not in memory['servers']:
            memory['servers'][target_id] = {}

        memory['servers'][target_id]['personality'] = personality.lower()
        self.save_memory(memory, guild_id=guild_id, user_id=user_id)

    def get_personality(self, guild_id=None, user_id=None):
        """Get the personality for a specific guild or user."""
        memory = self.load_memory(guild_id=guild_id, user_id=user_id)
        target_id = str(guild_id) if guild_id else f"user_{user_id}"
        # Fetch the personality from memory if available, otherwise return a default
        return memory.get("servers", {}).get(target_id, {}).get("personality", "wholesome")


    def load_memory(self, guild_id=None, user_id=None):
        """Load memory from the specific file for the guild or user."""
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

    def save_memory(self, memory, guild_id=None, user_id=None):
        """Save memory to the specific file for the guild or user."""
        if guild_id:
            memory_file = os.path.join(self.memory_dir, f"guild_{guild_id}.json")
        elif user_id:
            memory_file = os.path.join(self.memory_dir, f"user_{user_id}.json")
        else:
            return

        with open(memory_file, "w") as f:
            json.dump(memory, f, indent=4)
