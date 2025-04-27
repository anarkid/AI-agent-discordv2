import json
import os

class PersonalityHandler:
    def __init__(self, memory_file="memory.json"):
        self.memory_file = memory_file
        self.AVAILABLE_PERSONALITIES = self.load_personalities()

    def load_personalities(self):
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
        return self.AVAILABLE_PERSONALITIES

    def is_valid_personality(self, personality):
        return personality.lower() in self.AVAILABLE_PERSONALITIES

    def set_personality(self, guild_id, personality):
        memory = self.load_memory()
        if str(guild_id) not in memory['servers']:
            memory['servers'][str(guild_id)] = {}
        memory['servers'][str(guild_id)]['personality'] = personality.lower()
        self.save_memory(memory)

    def get_personality(self, guild_id):
        memory = self.load_memory()
        return memory.get("servers", {}).get(str(guild_id), {}).get("personality", "wholesome")

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return {"servers": {}}

    def save_memory(self, memory):
        with open(self.memory_file, "w") as f:
            json.dump(memory, f, indent=4)
