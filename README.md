# Discord Chat Bot

## 🧠 Возможности

- 💬 Отвечает на вопросы через команду `!ask`
- 🎭 Позволяет выбрать стиль ответа командой `!mode`
- 🤖 Работает с локальной LLM через Ollama (`http://localhost:11434`)
- 🔧 Поддержка кастомных промптов под каждый стиль

---

## 🚀 Установка

### 1. Установи Python 3.10 или новее

Скачать можно с официального сайта: https://www.python.org/downloads/

Убедись, что при установке ты выбрал `Add Python to PATH`.

---

### 2. Клонируй или скачай репозиторий

```bash
git clone https://github.com/yourusername/discord-ollama-bot.git
cd discord-ollama-bot
```
---

### 3.
Установи библиотеки:

```bash
pip install discord.py requests
```

### 4. Установи Ollama и модель
Скачай и установи Ollama: https://ollama.com

Запусти Ollama

Загрузите нужную модель (например, deepseek-r1:8b):

```bash
ollama pull deepseek-r1:8b
```

### 5. Закинь свой токен

```bash
bot.run("ТВОЙ_ТОКЕН_ЗДЕСЬ")
```

### 6. Запуск бота

```bash
python bot.py
```



### Возможные ошбки

"Cannot send an empty message" — ты пытаешься отправить пустой текст. Убедись, что все строки типа THINK_TEXTS[...] не пустые.

"Ошибка при подключении к Ollama" — проверь, что Ollama запущен, и модель загружена.

"400 Bad Request" — обычно из-за слишком длинного запроса. Старайся держать промпт до 4000 символов.
