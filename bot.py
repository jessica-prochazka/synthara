import os
import json
import discord
from discord import app_commands
import openai

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

WHITELIST_FILE = "whitelist.json"
OWNER_ID = 1265368042146238536


def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r") as f:
            return set(json.load(f))
    return {OWNER_ID}


def save_whitelist(whitelist):
    with open(WHITELIST_FILE, "w") as f:
        json.dump(list(whitelist), f)


whitelist = load_whitelist()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


@tree.command(name="add_user", description="Add a user to the whitelist")
@app_commands.describe(user="User to add")
async def add_user(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("You are not allowed to add users.", ephemeral=True)
        return
    whitelist.add(user.id)
    save_whitelist(whitelist)
    await interaction.response.send_message(f"Added {user.mention} to whitelist.", ephemeral=True)


@tree.command(name="gpt", description="Generate text using OpenAI")
@app_commands.describe(model="OpenAI model", prompt="Prompt text")
async def gpt(interaction: discord.Interaction, model: str, prompt: str):
    if interaction.user.id not in whitelist:
        await interaction.response.send_message("You are not in the whitelist.", ephemeral=True)
        return
    if not OPENAI_KEY:
        await interaction.response.send_message("OpenAI key not configured.", ephemeral=True)
        return
    openai.api_key = OPENAI_KEY
    try:
        response = openai.ChatCompletion.create(model=model, messages=[{"role": "user", "content": prompt}])
        result = response["choices"][0]["message"]["content"].strip()
        await interaction.response.send_message(result)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("DISCORD_BOT_TOKEN is not set")
    client.run(TOKEN)
