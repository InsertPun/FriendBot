import json
import discord
import asyncio
from discord.ext import commands
from gtts import gTTS
import ollama
#import speech_recognition as sr
#from discord_ext_audiorec import Recorder

with open("discord.json") as file:
    discord_related = json.load(file)

DISCORD_TOKEN = discord_related["DISCORD_TOKEN"]
TEXT_CHANNEL_ID = int(discord_related["TEXT_CHANNEL_ID"])
VOICE_CHANNEL_ID = int(discord_related["VOICE_CHANNEL_ID"])

intents = discord.Intents.default()
intents.message_content = True       # allow bot to read message content
intents.voice_states = True          # allow bot to detect voice channel join/leave

bot = commands.Bot(command_prefix="!", intents=intents)

# Short-term memory storage for conversation (last few messages)
conversation_history = []

def split_message(text, limit=2000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]

async def get_response(history):
    return await asyncio.to_thread(ollama.chat, model="deepseek-r1:1.5b", messages=history)

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
    if user_text == "!join" or user_text == "!leave" or user_text == "!shutdown":
        await bot.process_commands(message)
        return

    # Add user message to history
    conversation_history.append({"role": "user", "content": user_text})
    # Limit history to last 6 messages (3 exchanges)
    if len(conversation_history) > 6:
        conversation_history.pop(0)

    try:
        response = await get_response(conversation_history)
    except Exception as e:
        await message.channel.send("*(Error: could not get response from model)*")
        print("Model error:", e)
        return

    bot_reply = response["message"]["content"].strip() or "*[No response]*"
    bot_reply = bot_reply.replace("<think>", "").replace("</think>", "").strip()

    # Add bot response to history
    conversation_history.append({"role": "assistant", "content": bot_reply})
    if len(conversation_history) > 6:
        conversation_history.pop(0)

    for chunk in split_message(bot_reply):
        await message.channel.send(chunk)

    voice_client = message.guild.voice_client
    if voice_client and voice_client.is_connected():
        try:
            tts = gTTS(bot_reply, lang="en")
            tts.save("response.mp3")
            voice_client.play(discord.FFmpegPCMAudio("response.mp3"))
        except Exception as e:
            print("TTS/Audio error:", e)


@bot.command(name="join")
async def join(ctx):
    channel = ctx.guild.get_channel(VOICE_CHANNEL_ID)
    if channel:
        # Connect to the channel if not already connected.
        if ctx.voice_client is None:
            await channel.connect()
            await ctx.send(f"Joined {channel.name}")
        else:
            await ctx.send("Already connected to the voice channel")
    else:
        await ctx.send("Can't find voice channel")

@bot.command(name="leave")
async def leave(ctx):
    # Check if the bot is connected to a voice channel
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel")
    else:
        await ctx.send("Not connected to any voice channel")

@bot.command(name="shutdown")
async def shutdown(ctx):
    print("Shutdown command received!")
    await ctx.send("Shutting down...")
    await bot.close()

'''
async def finished_callback(sink, ctx):
    await ctx.send("Recording complete. Processing audio...")
    for user_id, audio in sink.audio_data.items():
        filename = f"recording-{user_id}.wav"
        audio.file.seek(0)
        with open(filename, "wb") as f:
            f.write(audio.file.read())

        recognizer = sr.Recognizer()
        with sr.AudioFile(filename) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                text = "Could not understand the audio."
            except sr.RequestError as e:
                text = f"STT service error: {e}"

        await ctx.send(f"Transcription for <@{user_id}>: {text}")
        os.remove(filename)


@bot.command(name="listen")
async def listen(ctx, duration: int = 5):
    vc = ctx.voice_client
    if vc is None:
        await ctx.send("I'm not connected to a voice channel. Use !join first.")
        return
    recorder = Recorder()
    await ctx.send(f"Recording for {duration} seconds...")
    vc.start_recording(recorder, finished_callback, ctx)
    await asyncio.sleep(duration)
    vc.stop_recording()
'''

# Start the bot
bot.run(DISCORD_TOKEN)
