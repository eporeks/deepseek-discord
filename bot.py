import discord
from discord.ext import commands
from discord import app_commands
import requests
import re
import asyncio

# Response styles
STYLES = {
    "normal": "",
    "gopnik": "Respond rudely and bluntly, using slang and colloquial expressions. Speak simply and briefly, like a regular street guy, with no polite formalities. Swearing makes it more fun, and explain as if you're annoyed by having to explain again.",
    "cutie": "Respond sweetly, like a kind and cute anime girl. Use lots of emojis, affectionate words, and a friendly tone. Speak softly, gently, and a bit playfully.",
    "intellectual": "Respond very politely and intellectually, using proper language, complex but clear formulations. Maintain a respectful tone and a cultured communication style."
}

# Ollama settings
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL_NAME = 'deepseek-r1:8b'

# Discord intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

MAX_DISCORD_MESSAGE_LEN = 2000
user_styles = {}

# Split message if too long
def split_message(text, max_length=MAX_DISCORD_MESSAGE_LEN):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

# View for response buttons
class ResponseView(discord.ui.View):
    def __init__(self, user_msg, bot_msg, prompt):
        super().__init__(timeout=300)
        self.user_msg = user_msg
        self.bot_msgs = bot_msg if isinstance(bot_msg, list) else [bot_msg]
        self.prompt = prompt

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.user_msg:
                try:
                    await self.user_msg.delete()
                except discord.NotFound:
                    pass
            for msg in self.bot_msgs:
                try:
                    await msg.delete()
                except discord.NotFound:
                    pass
            try:
                await interaction.message.delete()
            except discord.NotFound:
                pass
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Could not delete message:\n```{e}```", ephemeral=True)

    @discord.ui.button(label="Repeat", style=discord.ButtonStyle.secondary)
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
                raw_answer = data.get("response", "⚠️ Model did not return a response.")
                cleaned_answer = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip()
                chunks = split_message(cleaned_answer)

                await self.bot_msg.edit(content=chunks[0], view=self)

                for chunk in chunks[1:]:
                    await self.bot_msg.channel.send(chunk)

            else:
                await interaction.followup.send(f"❌ Error from Ollama: {response.status_code}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Connection error with Ollama:\n```{e}```", ephemeral=True)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("DeepSeek -> /mode"))
    await bot.tree.sync()
    print(f'Bot is running as {bot.user}')

@bot.tree.command(name="mode", description="Choose a response style")
async def mode_slash(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=False)

    embed = discord.Embed(
        title="Choose a response style",
        description=(
            "🎩 — Intellectual\n"
            "🐰 — Cutie\n"
            "💀 — Rude\n"
            "📄 — Normal style (default)\n\n"
            "Click a reaction below to choose your style."
        ),
        color=0x660d9e
    )
    msg = await interaction.channel.send(embed=embed)

    reactions = {
        "🎩": "intellectual",
        "🐰": "cutie",
        "💀": "rude",
        "📄": "normal"
    }

    for emoji in reactions:
        await msg.add_reaction(emoji)

    def check(reaction, user):
        return (
            user == interaction.user and
            reaction.message.id == msg.id and
            reaction.emoji in reactions
        )

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check)
    except asyncio.TimeoutError:
        timeout_msg = await interaction.channel.send("⌛ Time to choose a style has expired.")
        await asyncio.sleep(5)
        await msg.delete()
        await timeout_msg.delete()
        return

    chosen_style = reactions[reaction.emoji]
    user_styles[interaction.user.id] = chosen_style

    await bot.change_presence(activity=discord.Game({
        "intellectual": "📚 Intellectual",
        "cutie": "🌸 Anime girl",
        "rude": "STFU 🚬",
        "normal": "💬 Deepseek"
    }.get(chosen_style, "Ready!")))

    await msg.delete()
    await interaction.followup.send(f"✅ You chose the style: **{chosen_style}**", ephemeral=True)

@bot.tree.command(name="ask", description="Ask the AI a question")
@app_commands.describe(prompt="Your question for the bot")
async def ask_slash(interaction: discord.Interaction, prompt: str):
    thinking = await interaction.response.send_message("🤔 Thinking...", ephemeral=False)
    thinking_msg = await interaction.original_response()

    style = user_styles.get(interaction.user.id, "normal")
    style_prompt = STYLES.get(style, "")
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
            raw_answer = data.get("response", "⚠️ Model did not return a response.")
            cleaned_answer = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip()
            chunks = split_message(cleaned_answer)

            msg = await interaction.channel.send(chunks[0])
            view = ResponseView(user_msg=thinking_msg, bot_msg=msg, prompt=prompt)
            await msg.edit(view=view)

            await thinking_msg.delete()
        else:
            await interaction.followup.send(f"❌ Error from Ollama: {response.status_code}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Connection error with Ollama:\n```{e}```", ephemeral=True)

bot.run("YOUR_BOT_TOKEN_HERE")
