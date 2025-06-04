# 🤖 AI Personality Agent Discord Bot

*A modular, local LLM-powered Discord bot with dynamic personalities and short-term memory.*

---

## 🚀 Features

- 🧠 **Local Model Integration**  
  Works with local LLMs using Docker (via [Ollama](https://ollama.com/)).

- 🎭 **Personality Simulation**  
  Dynamic prompt engineering to simulate multiple AI personas.

- 💾 **Short-Term Memory**  
  Maintains contextual awareness with JSON-based memory storage.

- ⚙️ **Modular and Extensible**  
  Easily extendable architecture written in Python.


🧱 Architecture Overview
<pre>
 +-------------------------+
|  Python AI Agent Logic  |
+-----------+-------------+
            |
            v
+-------------------------+
|   Memory Engine Layer   |  ← Injects short-term memory context
+-----------+-------------+
            |
            v
+-------------------------+
|   Prompt Engine Layer   |  ← Injects personality into prompt
+-----------+-------------+
            |
            v
+-------------------------+
|   AI Model via Docker   |  ← Local inference (e.g., Ollama)
+-------------------------+

</pre>

## 📁 File Structure
<pre>
.
├── bot.py # Main entry script (Discord bot)
├── cogs/ # Discord command modules
│ ├── general.py # Utility commands
│ └── reply.py # Personality-based replies
│
├── handlers/ # Core functionality
│ ├── filehandler.py # File operations (config/logs)
│ ├── memory_handler.py # Temporary memory storage
│ ├── personalityhandler.py # Personality management
│ ├── prompt_builder.py # Structured prompt generation
│ └── response_handler.py # Response parsing and formatting
│
├── utility/
│ └── personalities/ # JSON-defined personalities
│ └── default.json
│
├── requirements.txt # Python dependencies
├── .gitignore # Git exclusions
└── README.md # You’re here!
</pre>

---

## 📦 Requirements

- Python **3.13+**
- Docker **20.10+**
- RAM: **16GB+ recommended**
- Optional: **NVIDIA GPU** for acceleration

### 🔧 Install Dependencies

bash
```pip install -r requirements.txt```

🐳 Local LLM Setup (via Ollama)

Pull the Docker Image
```
docker pull ollama/ollama
```
Run the Container
```
docker run -d --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama
```
Load a Model
```docker exec -it ollama ollama run llama3```
or
```docker exec -it ollama ollama run mistral```

API Access

```Endpoint: http://localhost:11434/api/generate```

(Optional) Enable GPU (Linux + NVIDIA)
```
docker run -d --gpus all \
  --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama
```

⚙️ Configuration
🔑 Before First Run

  Replace the token in bot.py with your Discord bot token.

  Update the LLM model name in reply.py with your installed model (e.g., llama3, mistral).

🎭 Personality Profiles

Define custom personalities in utility/personalities/.

Example: default.json
```
{
  "personality": "personality description"
}
```
💬 Bot Commands
| Command        | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| `!reply <msg>` | Ask a question or interact with uploaded PDF/DOCX/TXT/PPTX files.           |
| `!commands`    | Lists all available commands.                                               |
| `!forget`      | Clears short-term memory for the server or DM.                              |
| `!chooseTone`  | Opens a menu to select a personality.                                       |
| `!getTone`     | Displays the current active personality.                                    |

🔄 Personality Switching
    - Shows a paginated menu (5 personalities per page).
    - Only the invoking user can make a selection.
    - Personality persists between sessions.
    - !forget does not reset chosen tone.

🔮 Future Improvements
    - ✅ Persistent personality storage via database
    - ✅ Voice chat support with text-to-speech and transcription
    - ✅ Export responses as .txt or .md files

📣 Contributions

Contributions are welcome! Fork, modify, and send a pull request.
