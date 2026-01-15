from pyflowchart import Flowchart

code = """\
import discord
import sqlite3
from discord import app_commands
from discord.ext import tasks, commands
import random
import os
from ai_art import generate_image

intents = discord.Intents.all()
# database stuff
database = sqlite3.connect('database.db')
cursor = database.cursor()
database.execute("CREATE TABLE IF NOT EXISTS story(story_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, story_text STRING)")
database.execute("CREATE TABLE IF NOT EXISTS story_images(image_id INTEGER PRIMARY KEY AUTOINCREMENT, story_id INTEGER, image_path TEXT, FOREIGN KEY (story_id) REFERENCES story(story_id) ON DELETE CASCADE)")

def run_discord_bot():
    TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix='-', intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')
        try:
            synced = await client.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

    @client.tree.command(name="prompts")
    @app_commands.describe(prompt="Give me your prompts for the story")
    async def hello(interaction: discord.Interaction, prompt: str):
        await interaction.response.send_message(f"{interaction.user.mention} said: `{prompt}`\\n")
        query = "INSERT INTO messages VALUES (?, ?)"
        cursor.execute(query, (prompt, interaction.user.id))
        database.commit()

    client.run(TOKEN)
"""

fc = Flowchart.from_code(code)
print(fc.flowchart())
