# Discord Chat Bot

### 🆕 New functions



## 🧠 Features

* 💬 Answers questions using the `!ask` command
* 🎭 Allows switching response styles with the `!mode` command
* 🤖 Works with a local LLM via Ollama (`http://localhost:11434`)
* 🔧 Supports custom prompts for each style

---

## 🚀 Installation

### 1. Install Python 3.10 or newer

You can download it from the official website: [https://www.python.org/downloads/](https://www.python.org/downloads/)

Make sure to select `Add Python to PATH` during installation.

---

### 2. Clone or download the repository

```bash
git clone https://github.com/yourusername/discord-ollama-bot.git
cd discord-ollama-bot
```

---

### 3. Install dependencies:

```bash
pip install discord.py requests
```

---

### 4. Install Ollama and a model

Download and install Ollama: [https://ollama.com](https://ollama.com)

Start Ollama.

Download the required model (e.g., deepseek-r1:8b):

```bash
ollama pull deepseek-r1:8b
```

---

### 5. Add your bot token

```bash
bot.run("YOUR_TOKEN_HERE")
```

---

### 6. Run the bot

```bash
python bot.py
```

---

### Possible Errors

* **"Cannot send an empty message"** — You’re trying to send an empty string. Make sure all THINK\_TEXTS\[...] lines are not empty.

* **"Error connecting to Ollama"** — Make sure Ollama is running and the model is loaded.

* **"400 Bad Request"** — Usually due to a prompt being too long. Try to keep it under 4000 characters.

---
