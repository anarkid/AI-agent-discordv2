# 🤖 AI Personality Agent Discord Bot  

*A modular, local LLM-powered Discord bot with dynamic personalities and memory*

---

## 🚀 Features

- 🧠 **Local Model Integration**  
  Works with local LLMs using Docker (Ollama integration).

- 🎭 **Personality Simulation**  
  Leverages dynamic prompt engineering to simulate multiple AI personas.

- 💾 **Short-Term Memory**  
  Retains conversation context using JSON-based memory storage.

- ⚙️ **Modular and Extensible**  
  Easy-to-extend architecture written in Python.

---

## 🧱 Architecture Overview

+-------------------------+
|  Python AI Agent Logic  |
+-----------+-------------+
      	    |
	          v
+-------------------------+
|   Memory Engine Layer   | ← Context injection from memory
+-----------+-------------+
	          |
	          v
+-------------------------+
|   Prompt Engine Layer   | ← Personality injection
+-----------+-------------+
	          |
	          v
+-------------------------+
|   AI Model via Docker   | ← Local LLM inference (e.g., Ollama)
+-------------------------+


---

📁 File Structure

.
├── bot.py                      # Main entry script (Discord bot)
├── cogs/                       # Discord command modules
│   ├── general.py              # Utility commands
│   └── reply.py                # Personality-based replies
│
├── handlers/                   # Core functionality
│   ├── filehandler.py          # File operations (config/logs)
│   ├── memory_handler.py       # Temporary memory storage
│   ├── personalityhandler.py   # Personality management
│   ├── prompt_builder.py       # Structured prompt generation
│   └── response_handler.py     # Response parsing and formatting
│
├── utility/
│   └── personalities/          # JSON-defined personalities
│       └── default.json
│
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git exclusions
└── README.md                   # You’re here!

## 📦 Requirements

- Python **3.13+**
- Docker **20.10+**
- RAM: **16GB+ recommended**
- Optional: **NVIDIA GPU** for hardware acceleration

Install dependencies:

pip install -r requirements.txt

🐳 Local LLM Setup (via Ollama)
1. Pull the Ollama Docker Image

docker pull ollama/ollama

2. Run the Container

docker run -d --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama

3. Load a Model

Inside the container:

docker exec -it ollama ollama run llama3
# or
docker exec -it ollama ollama run mistral

4. Access the Ollama API

    Endpoint: http://localhost:11434/api/generate

5. Optional: Enable GPU (Linux + NVIDIA)

docker run -d --gpus all \
  --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama


### 💬 Reminder
Before using the bot: 
  -change the token in bot.py with your discord bot token
  -change the LLM model in reply.py with your installed LLM model 

🔧 Configuration: Personality Profiles

Define personality behavior by creating a JSON file in utility/personalities/.

Example: default.json

{
  "personality": "A sarcastic, witty assistant that enjoys playful banter."
}

### 💬 Bot Commands

| Command          | Description                                                                |
|------------------|----------------------------------------------------------------------------|
| `!reply <msg>`   | Ask the bot a question or interact with uploaded PDF/DOCX/TXT/PPTX files. 	|
| `!commands`      | Lists all available commands.                                              |
| `!forget`        | Clears short-term memory for the server or DM.                             |
| `!chooseTone`    | Opens a menu to select a personality.                                      |
| `!getTone`       | Displays the current active personality.                                   |

🔄 Personality Switching

When you use !chooseTone, the bot will:

    Show a paginated menu with up to 5 personalities per page.

    Allow only the user who invoked the command to make a selection.

    Save your choice and persist it across future interactions.

    Personality settings remain intact even after memory is cleared with !forget.


🔮 Future Improvements

    Store personalities in a persistent DB
    Integrating text-to-speech and transcription to the discord bot for voice chat
    Allow the bot to export responses in .txt or .md format

