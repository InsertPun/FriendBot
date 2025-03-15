import json
import discord
from discord.ext import commands
import ollama

with open("discord.json") as file:
    discord_related = json.load(file)

DISCORD_TOKEN = discord_related["DISCORD_TOKEN"]
TEXT_CHANNEL_ID = int(discord_related["TEXT_CHANNEL_ID"])
VOICE_CHANNEL_ID = int(discord_related["VOICE_CHANNEL_ID"])

# Set up intents (to listen to messages and voice state events)
intents = discord.Intents.default()
intents.message_content = True       # allow bot to read message content
intents.voice_states = True          # allow bot to detect voice channel join/leave

bot = commands.Bot(command_prefix="!", intents=intents)

# Short-term memory storage for conversation (last few messages)
conversation_history = []

@bot.event
async def on_ready():
    print(f"FriendBot has logged in as {bot.user}")

@bot.event
async def on_message(message):
    # Ignore messages from bots (including itself) or wrong channel
    if message.author.bot:
        return
    if message.channel.id != TEXT_CHANNEL_ID:
        return

    user_text = message.content.strip()
    if user_text == "":
        return  # ignore empty messages

    # Add user message to history
    conversation_history.append({"role": "user", "content": user_text})
    # Limit history to last 6 messages (3 exchanges)
    if len(conversation_history) > 6:
        conversation_history.pop(0)

    try:
        response = ollama.chat(model="deepseek-r1:1.5b", messages=conversation_history)
    except Exception as e:
        await message.channel.send("*(Error: could not get response from model)*")
        print("Model error:", e)
        return

    bot_reply = response["message"]["content"].strip()
    if bot_reply == "":
        bot_reply = "*[No response]*"

    # Add bot response to history
    conversation_history.append({"role": "assistant", "content": bot_reply})
    if len(conversation_history) > 6:
        conversation_history.pop(0)

    # Send the text response in the channel
    await message.channel.send(bot_reply)

# Start the bot
bot.run(DISCORD_TOKEN)
