import os
import json
import logging
from datetime import datetime, date

import discord
from discord import app_commands
from discord.ext import commands
import openai

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord_bot")

TOKEN_LOG_FILE = "token_usage.txt"
OPENAI_KEY_FILE = "openai_key.txt"
DISCORD_TOKEN_FILE = "discord_token.txt"
WHITELIST_FILE = "whitelist.json"
BLACKLIST_FILE = "blacklist.json"
PRO_USERS_FILE = "pro_users.json"

OWNER_ID = 1265368042146238536
BOT_VERSION = "v1"

WHITELIST: dict[int, str] = {}
PRO_USERS: set[int] = set()
BLACKLIST: set[int] = set()

def load_json(path: str, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return default
    return default

def save_json(path: str, data) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass

def load_state() -> None:
    global WHITELIST, PRO_USERS, BLACKLIST
    WHITELIST = load_json(WHITELIST_FILE, {})
    PRO_USERS = set(load_json(PRO_USERS_FILE, []))
    BLACKLIST = set(load_json(BLACKLIST_FILE, []))
    WHITELIST.setdefault(OWNER_ID, datetime.utcnow().date().isoformat())

def save_state() -> None:
    save_json(WHITELIST_FILE, WHITELIST)
    save_json(PRO_USERS_FILE, list(PRO_USERS))
    save_json(BLACKLIST_FILE, list(BLACKLIST))

class GPTBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        WHITELIST.setdefault(OWNER_ID, datetime.utcnow().date().isoformat())
        save_state()

load_state()
bot = GPTBot()

# Helper functions

def log_tokens(user_id: int, tokens: int):
    timestamp = datetime.utcnow().isoformat()
    with open(TOKEN_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp},{user_id},{tokens}\n")

def token_usage_stats(user_id: int):
    daily = monthly = total = 0
    today = date.today()
    month_start = today.replace(day=1)
    if os.path.exists(TOKEN_LOG_FILE):
        with open(TOKEN_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ts_str, uid_str, tok_str = line.strip().split(",")
                    if int(uid_str) != user_id:
                        continue
                    dt = datetime.fromisoformat(ts_str)
                    tokens = int(tok_str)
                    total += tokens
                    if dt.date() == today:
                        daily += tokens
                    if dt.date() >= month_start:
                        monthly += tokens
                except ValueError:
                    continue
    return daily, monthly, total

def get_openai_key() -> str | None:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    try:
        with open(OPENAI_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def get_discord_token() -> str | None:
    token = os.getenv("DISCORD_TOKEN")
    if token:
        return token
    try:
        with open(DISCORD_TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

async def chat_gpt(model_alias: str, prompt: str):
    openai.api_key = get_openai_key()
    model = API_MODEL_MAP.get(model_alias, model_alias)
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    tokens = response["usage"]["total_tokens"]
    return response.choices[0].message.content.strip(), tokens

# Command checks

def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == OWNER_ID

def is_whitelisted(interaction: discord.Interaction) -> bool:
    return interaction.user.id in WHITELIST

def has_pro(interaction: discord.Interaction) -> bool:
    return interaction.user.id in PRO_USERS

# Slash Commands

@bot.tree.command(name="about", description="Show version")
@app_commands.check(lambda i: is_whitelisted(i) or is_owner(i))
async def about(interaction: discord.Interaction):
    await interaction.response.send_message(f"Bot version: {BOT_VERSION}")

@bot.tree.command(name="ping", description="Ping the bot")
@app_commands.check(lambda i: is_whitelisted(i) or is_owner(i))
async def ping(interaction: discord.Interaction):
    latency_ms = int(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! {latency_ms}ms")

@bot.tree.command(name="info", description="Show user info")
async def info(interaction: discord.Interaction):
    user = interaction.user
    if user.id in BLACKLIST:
        await interaction.response.send_message("Blacklisted", ephemeral=True)
        return
    if user.id not in WHITELIST:
        await interaction.response.send_message("Sorry, you are not whitelisted.", ephemeral=True)
        return
    pro_status = user.id in PRO_USERS
    daily, monthly, total = token_usage_stats(user.id)
    embed = discord.Embed(title=user.name, description=f"Pro: {pro_status}")
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="ID", value=str(user.id), inline=False)
    embed.add_field(name="Tokens (daily)", value=str(daily), inline=True)
    embed.add_field(name="Tokens (monthly)", value=str(monthly), inline=True)
    embed.add_field(name="Tokens (total)", value=str(total), inline=True)
    embed.add_field(name="Whitelisted seit", value=WHITELIST.get(user.id, "?"), inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

MODELS = [
    "gpt-4",
    "4o",
    "4.1",
    "4.1-mini",
    "o1",
    "o1-pro",
    "o3",
    "o3-mini",
    "o3-mini-high",
    "o3-pro",
]

API_MODEL_MAP = {
    "gpt-4": "gpt-4",
    "4o": "gpt-4o",
    "4.1": "gpt-4-turbo",
    "4.1-mini": "gpt-4-turbo",
    "o1": "gpt-3.5-turbo",
    "o1-pro": "gpt-4-turbo",
    "o3": "gpt-3.5-turbo",
    "o3-mini": "gpt-3.5-turbo",
    "o3-mini-high": "gpt-3.5-turbo",
    "o3-pro": "gpt-4-turbo",
}

@bot.tree.command(name="gpt", description="ChatGPT prompt")
@app_commands.describe(prompt="Prompt", web_search="Enable web search")
@app_commands.choices(model=[app_commands.Choice(name=m, value=m) for m in MODELS])
async def gpt(
    interaction: discord.Interaction,
    model: app_commands.Choice[str],
    prompt: str,
    attachment: discord.Attachment | None = None,
    web_search: bool = False,
):
    model_value = model.value
    user = interaction.user
    if user.id not in WHITELIST or user.id in BLACKLIST:
        await interaction.response.send_message("Sorry, you are not whitelisted.", ephemeral=True)
        return
    if model_value.endswith("-pro") and user.id not in PRO_USERS:
        embed = discord.Embed(
            description=f"Sorry, you're not an authorized Pro user for this model ({model_value}).",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if attachment:
        prompt += f"\nAttachment URL: {attachment.url}"
    output, tokens = await chat_gpt(model_value, prompt)
    log_tokens(user.id, tokens)
    embed = discord.Embed(description=output)
    embed.set_author(name=model_value)
    embed.set_footer(text=prompt)
    await interaction.response.send_message(embed=embed)

# Admin commands

@bot.tree.command(name="user-panel", description="Admin operations")
@app_commands.check(is_owner)
async def user_panel(interaction: discord.Interaction, action: str, user: discord.User):
    if action == "whitelist":
        WHITELIST[user.id] = datetime.utcnow().date().isoformat()
        save_state()
        await interaction.response.send_message(f"{user} whitelisted")
    elif action == "blacklist":
        BLACKLIST.add(user.id)
        WHITELIST.pop(user.id, None)
        save_state()
        await interaction.response.send_message(f"{user} blacklisted")
    elif action == "set-pro":
        PRO_USERS.add(user.id)
        save_state()
        await interaction.response.send_message(f"{user} set to pro")
    elif action == "view-stats":
        d, m, t = token_usage_stats(user.id)
        await interaction.response.send_message(f"Tokens - daily: {d}, monthly: {m}, total: {t}")
    else:
        await interaction.response.send_message("Unknown action", ephemeral=True)

token = get_discord_token()
if not token:
    raise RuntimeError("Discord token not provided")
bot.run(token)

