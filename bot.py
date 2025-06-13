import discord
from discord.ext import commands
from discord import app_commands
import requests
import re
import asyncio

# Response styles
STYLES = {
    "normal": "",
    "rude": "Respond rudely and directly, using slang and informal language. Keep it short and simple, like a street guy. Add some swearing for fun and sound annoyed as if you're tired of being asked to explain.",
    "cute": "Respond sweetly, like a kind and cute anime girl. Use lots of emojis, affectionate words, and a friendly tone. Speak gently, lightly, and playfully.",
    "smart": "Respond very politely and intelligently. Use proper language, clear and complex but understandable expressions. Maintain a respectful and cultured tone."
}

# Ollama settings
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL_NAME = 'deepseek-r1:8b'

# Discord intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

MAX_DISCORD_MESSAGE_LEN = 2000
user_styles = {}

def split_message(text, max_length=MAX_DISCORD_MESSAGE_LEN):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

class ResponseView(discord.ui.View):
    def __init__(self, user_msg, bot_msgs, prompt):
        super().__init__(timeout=300)
        self.user_msg = user_msg
        self.bot_msgs = bot_msgs
        self.prompt = prompt

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.user_msg.delete()
            for msg in self.bot_msgs:
                await msg.delete()
            await interaction.message.delete()
        except Exception as e:
            await interaction.response.send_message(f"Error deleting messages: {e}", ephemeral=True)

    @discord.ui.button(label="Regenerate", style=discord.ButtonStyle.secondary)
    async def repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        style = user_styles.get(interaction.user.id, "normal")
        style_prompt = STYLES.get(style, "")
        full_prompt = f"{style_prompt}\n\nQuestion: {self.prompt}" if style_prompt else self.prompt

        payload = {
            "model": MODEL_NAME,
            "prompt": full_prompt,
            "stream": False
        }

        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=60)
            if response.ok:
                data = response.json()
                raw_answer = data.get("response", "⚠️ No response from the model.")
                cleaned_answer = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip()
                chunks = split_message(cleaned_answer)

                sent_msgs = []
                for chunk in chunks:
                    m = await interaction.channel.send(chunk)
                    sent_msgs.append(m)

                new_view = ResponseView(user_msg=self.user_msg, bot_msgs=sent_msgs, prompt=self.prompt)
                await interaction.followup.send(view=new_view)
            else:
                await interaction.followup.send(f"❌ Error from Ollama: {response.status_code}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error connecting to Ollama:\n```{e}```")

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("Waiting for commands..."))
    print(f'Bot is running as {bot.user}')

@bot.command()
async def mode(ctx):
    embed = discord.Embed(title="Choose a response style", description=(
        "🎩 — Smart\n"
        "🐰 — Cute\n"
        "💀 — Rude\n"
        "📄 — Normal (default)\n\n"
        "React below to choose a style."
    ), color=0x660d9e)
    msg = await ctx.send(embed=embed)

    reactions = {
        "🎩": "smart",
        "🐰": "cute",
        "💀": "rude",
        "📄": "normal"
    }

    for emoji in reactions:
        await msg.add_reaction(emoji)

    def check(reaction, user):
        return user == ctx.author and reaction.message.id == msg.id and reaction.emoji in reactions

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await msg.edit(content="⌛ Time to choose a style has expired.", embed=None)
        return

    chosen_style = reactions[reaction.emoji]
    user_styles[ctx.author.id] = chosen_style

    # Update status message
    await bot.change_presence(activity=discord.Game(f"Selected style: {chosen_style}"))

    await msg.delete()
    await ctx.send(f"✅ You selected style: **{chosen_style}**", delete_after=4)

@bot.command()
async def ask(ctx, *, prompt):
    style = user_styles.get(ctx.author.id, "normal")
    style_prompt = STYLES.get(style, "")
    think_status = {
        "smart": "🎩 Thinking...",
        "cute": "☺️ Thinking about your question...",
        "rude": "Hold on, I'll say something...",
        "normal": "🧠 Thinking..."
    }

    thinking_msg = await ctx.send(think_status.get(style, "🧠 Thinking..."))

    full_prompt = f"{style_prompt}\n\nQuestion: {prompt}" if style_prompt else prompt

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.ok:
            data = response.json()
            raw_answer = data.get("response", "⚠️ No response from the model.")
            cleaned_answer = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip()

            await thinking_msg.delete()

            chunks = split_message(cleaned_answer)
            sent_msgs = []
            for chunk in chunks:
                m = await ctx.send(chunk)
                sent_msgs.append(m)

            view = ResponseView(user_msg=ctx.message, bot_msgs=sent_msgs, prompt=prompt)
            await ctx.send(view=view)
        else:
            await thinking_msg.edit(content=f"❌ Error from Ollama: {response.status_code}")
    except Exception as e:
        await thinking_msg.edit(content=f"❌ Error connecting to Ollama:\n```{e}```")

# Replace your token here
bot.run("YOUR_DISCORD_BOT_TOKEN_HERE")
