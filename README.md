# Synthara Discord Bot

This repository contains a simple Discord bot using `discord.py`.

## Configuration

The bot looks for two environment variables when running:

- `DISCORD_TOKEN` – the Discord bot token.
- `OWNER_ID` – the numeric Discord ID of the bot owner.

User information is stored in `user_stats.json`. This file is created
automatically when the bot runs for the first time.

## Slash Commands

* `/ping` – return the current gateway latency.
* `/uptime` – show how long the bot has been running.
* `/remove_user <ID>` – delete a user from the whitelist. Only the owner
  can run this command.
* `/config-user <set-pro|view-stats> <ID>` – mark a user as pro or view
  their usage statistics.
* `/model <model>` – request a model. If the model is considered
  pro‑only (for example `gpt-4`), non‑pro users will receive the message
  "Sorry, you're not authenticated to use this model".

## User Statistics

Each user entry in `user_stats.json` stores:

- `is_pro` – whether the user has access to pro-only models.
- `command_count` – how many commands the user has issued.
- `token_usage` – cumulative token usage (placeholder value).
- `last_use` – ISO timestamp of the last command used.

Statistics are updated whenever a slash command is executed.
