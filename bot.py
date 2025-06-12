import discord
from discord.ext import commands
import requests
import re
import asyncio

# Промпты стилей
STYLES = {
    "нормальный": "",
    "быдло": "Отвечай грубо и прямо, используй сленг и разговорные выражения. Говори просто и коротко, будто обычный парень с улицы, без вежливых формальностей.",
    "няшка": "Отвечай мило, как добрая и милая девочка-няшка. Используй много эмодзи, ласковые слова и дружелюбный тон. Говори легко, нежно и немного игриво.",
    "интеллигент": "Отвечай очень вежливо и интеллигентно, используй правильную речь, сложные, но понятные формулировки. Поддерживай уважительный тон и культурный стиль общения."
}

# Тексты "думаю..." по стилю
THINK_TEXTS = {
    "нормальный": "❗ Думаю... ❗",
    "быдло": "Ща выдам хуйню какую-то... 🖕🖕🖕",
    "няшка": "☺️ Думаю над твоим вопросом...",
    "интеллигент": "🎩 Обдумываю ваш вопрос... 🧠"
}

# Настройки Ollama
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL_NAME = 'deepseek-r1:8b' #Указать свою модель, которую скачали

# Discord intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

MAX_DISCORD_MESSAGE_LEN = 2000

def split_message(text, max_length=MAX_DISCORD_MESSAGE_LEN):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

user_styles = {}

@bot.event
async def on_ready():
    print(f'Бот запущен как {bot.user}')

@bot.command()
async def mode(ctx):
    embed = discord.Embed(title="Выбери стиль ответа", description=(
        "🎩 — Интеллигент\n"
        "🐰 — Няшка\n"
        "💀 — Быдло\n"
        "📄 — Нормальный стиль (по умолчанию)\n\n"
        "Нажми на реакцию ниже, чтобы выбрать стиль."
    ), color=0x7f127f)
    message = await ctx.send(embed=embed)

    reactions = {
        "🎩": "интеллигент",
        "🐰": "няшка",
        "💀": "быдло",
        "📄": "нормальный"
    }

    for r in reactions.keys():
        await message.add_reaction(r)

    def check(reaction, user):
        return user == ctx.author and reaction.message.id == message.id and reaction.emoji in reactions

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await message.edit(content="⌛ Время выбора стиля истекло.", embed=None)
        return

    chosen_style = reactions[reaction.emoji]
    user_styles[ctx.author.id] = chosen_style
    await message.edit(content=f"✅ Ты выбрал стиль: **{chosen_style}**", embed=None)

@bot.command()
async def ask(ctx, *, prompt):
    style = user_styles.get(ctx.author.id, "нормальный")
    style_prompt = STYLES.get(style, "")
    think_text = THINK_TEXTS.get(style, "❗ Думаю... ❗")

    thinking_msg = await ctx.send(think_text)

    if style_prompt:
        full_prompt = f"{style_prompt}\n\nВопрос: {prompt}"
    else:
        full_prompt = prompt

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.ok:
            data = response.json()
            raw_answer = data.get("response", "⚠️ Модель не вернула ответ.")
            cleaned_answer = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip()

            await thinking_msg.delete()

            for chunk in split_message(cleaned_answer):
                await ctx.send(chunk)
        else:
            await thinking_msg.edit(content=f"❌ Ошибка от Ollama: {response.status_code}")
    except Exception as e:
        await thinking_msg.edit(content=f"❌ Ошибка при подключении к Ollama:\n```{e}```")

bot.run("") #Токен бота
