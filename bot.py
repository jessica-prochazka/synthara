import json
import os
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

DATA_FILE = 'user_stats.json'
OWNER_ID = int(os.environ.get('OWNER_ID', '0'))
PRO_MODELS = {'gpt-4', 'gpt-4-32k'}

start_time = datetime.utcnow()


def load_data():
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_user(data, uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {
            'is_pro': False,
            'command_count': 0,
            'token_usage': 0,
            'last_use': None,
        }
    return data[uid]


def update_usage(uid, tokens=0):
    data = load_data()
    user = get_user(data, uid)
    user['command_count'] += 1
    user['token_usage'] += tokens
    user['last_use'] = datetime.utcnow().isoformat()
    save_data(data)


def is_pro(uid):
    data = load_data()
    return get_user(data, uid).get('is_pro', False)


def check_pro_model(uid, model):
    if model in PRO_MODELS and not is_pro(uid):
        return False
    return True


intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')


@bot.tree.command(name='ping', description='Return the gateway ping')
async def ping(interaction: discord.Interaction):
    update_usage(interaction.user.id)
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f'Pong! {latency_ms} ms')


@bot.tree.command(name='uptime', description='Show how long the bot has been running')
async def uptime(interaction: discord.Interaction):
    update_usage(interaction.user.id)
    delta = datetime.utcnow() - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    await interaction.response.send_message(f'Uptime: {hours}h {minutes}m {seconds}s')


@bot.tree.command(name='remove_user', description='Delete a user from the whitelist')
async def remove_user(interaction: discord.Interaction, user_id: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message('You do not have permission to use this command.', ephemeral=True)
        return
    data = load_data()
    if user_id in data:
        del data[user_id]
        save_data(data)
        await interaction.response.send_message(f'Removed user {user_id}', ephemeral=True)
    else:
        await interaction.response.send_message('User not found.', ephemeral=True)


@bot.tree.command(name='config-user', description='Set pro status or view user stats')
@app_commands.describe(action='"set-pro" to grant pro access, "view-stats" to show usage stats', user_id='Target user ID')
async def config_user(interaction: discord.Interaction, action: str, user_id: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message('You do not have permission to use this command.', ephemeral=True)
        return
    data = load_data()
    user = get_user(data, user_id)
    if action == 'set-pro':
        user['is_pro'] = True
        save_data(data)
        await interaction.response.send_message(f'User {user_id} marked as pro.', ephemeral=True)
    elif action == 'view-stats':
        msg = (f"Pro: {user['is_pro']}, Commands: {user['command_count']}, "
               f"Tokens: {user['token_usage']}, Last use: {user['last_use']}")
        await interaction.response.send_message(msg, ephemeral=True)
    else:
        await interaction.response.send_message('Invalid action.', ephemeral=True)


@bot.tree.command(name='model', description='Request a model (demo)')
async def model_cmd(interaction: discord.Interaction, model: str):
    update_usage(interaction.user.id)
    if not check_pro_model(interaction.user.id, model):
        await interaction.response.send_message("Sorry, you're not authenticated to use this model", ephemeral=True)
        return
    await interaction.response.send_message(f'Model {model} accepted (dummy response)')


def run():
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        raise RuntimeError('DISCORD_TOKEN environment variable not set')
    bot.run(token)


if __name__ == '__main__':
    run()
