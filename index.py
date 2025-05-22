import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int("1249933684539396149")
REQUIRED_ROLE_ID = int("339310858148249632")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

tree = bot.tree

# Load keys from a text file
def load_keys():
    with open("keys.txt", "r") as f:
        return [line.strip() for line in f.readlines()]

# Load users from a JSON file
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return {}

# Save users to a JSON file
def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

# Ensure the key is unique and hasn't been given out before
def get_unique_key(used_keys, available_keys):
    for key in available_keys:
        if key not in used_keys:
            return key
    return None

# Gen Modal for inputting username/password
class GenModal(discord.ui.Modal, title="Generate Key"):
    username = discord.ui.TextInput(label="Username", required=True)
    password = discord.ui.TextInput(label="Password", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        users = load_users()
        if self.username.value in users and users[self.username.value]["password"] == self.password.value:
            user_data = users[self.username.value]
            used_keys = [user["key"] for user in users.values() if "key" in user]
            available_keys = load_keys()

            # Check if user already has a key
            if "key" in user_data:
                await interaction.response.send_message("You already have a key.", ephemeral=True)
                return
            
            # Get a unique key
            key = get_unique_key(used_keys, available_keys)
            if key:
                user_data["key"] = key
                save_users(users)
                await interaction.response.send_message(f"Here is your key: {key}", ephemeral=True)
            else:
                await interaction.response.send_message("No available keys left.", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid username or password.", ephemeral=True)

# Command for generating a key
@tree.command(name="gen", description="Generate a Key (with username/password)")
async def gen(interaction: discord.Interaction):
    await interaction.response.send_modal(GenModal())

# Command for creating a new user
@tree.command(name="create", description="Owner only: Create a new user")
@app_commands.describe(username="Username", password="Password")
async def create(interaction: discord.Interaction, username: str, password: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return
    
    users = load_users()
    
    # If username already exists, notify the user
    if username in users:
        await interaction.response.send_message("This username already exists.", ephemeral=True)
        return
    
    users[username] = {
        "password": password
    }

    save_users(users)
    await interaction.response.send_message(f"User `{username}` created successfully.", ephemeral=True)

# Event when bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await tree.sync()

bot.run(TOKEN)
