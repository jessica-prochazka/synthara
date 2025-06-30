# Synthara Discord Bot

This repository contains a simple Discord bot that uses slash commands to
interact with the OpenAI API.

## Commands

- `/gpt <model> <prompt>` – generate text using the specified OpenAI model.
- `/add_user <user>` – add a user to the whitelist. Only the owner can use
  this command.

## Configuration

Set the following environment variables before running the bot:

- `DISCORD_BOT_TOKEN` – your Discord bot token.
- `OPENAI_API_KEY` – API key for OpenAI.

The whitelist is stored in `whitelist.json` in the working directory. The
owner's ID (1265368042146238536) is always allowed and is the only account that
can add other users to the whitelist.

Run the bot with `python bot.py`.
