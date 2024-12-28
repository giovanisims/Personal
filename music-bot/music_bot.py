import discord  
import os  
import asyncio  
import yt_dlp  
from collections import deque  
from dotenv import load_dotenv  
import logging  
import random

logging.basicConfig(level=logging.INFO)

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    intents = discord.Intents.default()
    intents.message_content = True  
    client = discord.Client(intents=intents)

    voice_clients = {}
    song_queues = {}

    ytdl_options = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,  # Allow deeper info extraction  
        "noplaylist": False,
        "nocheckcertificate": True,
    }
    ytdl = yt_dlp.YoutubeDL(ytdl_options)
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -af "volume=0.5"'
    }

    async def play_next(guild_id):
        if guild_id in song_queues and song_queues[guild_id]:
            try:
                song = song_queues[guild_id].popleft()
                loop = asyncio.get_event_loop()

                # Process the song URL in a thread pool for responsiveness  
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(song['url'], download=False))

                if data and 'url' in data:
                    player = discord.FFmpegPCMAudio(data['url'], **ffmpeg_options)
                    voice_clients[guild_id].play(
                        player,
                        after=lambda e: asyncio.run_coroutine_threadsafe(
                            play_next(guild_id),
                            client.loop  
                        ).result()
                    )
            except Exception as e:
                logging.error(f"Error in play_next: {str(e)}")
                await asyncio.sleep(1)
                asyncio.run_coroutine_threadsafe(play_next(guild_id), client.loop)
        else:
            logging.warning("Queue is empty or does not exist.")

    async def process_playlist_entry(entry, guild_id):
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(entry['url'], download=False))
            formats = data.get('formats', [])
            logging.info(f"Formats for entry: {formats}")  # Log available formats
            
            audio_url = next((f.get('url') for f in formats if f.get('acodec') != 'none'), None)
            if audio_url:
                song_queues[guild_id].append({'url': audio_url, 'title': data.get('title', 'Unknown')})
                logging.info(f"Added {data.get('title', 'Unknown')} to queue")
            else:
                logging.warning(f"No audio format found for {data.get('title', 'Unknown')}")
        except yt_dlp.DownloadError as e:
            logging.error(f"Error with entry {entry.get('title', 'Unknown')}: {str(e)}")

    async def process_single_track(data, guild_id, message):
        logging.info(f"Processing single track: {data.get('title', 'Unknown')}")
        formats = data.get('formats', [])
        logging.info(f"Available formats: {formats}")  # Log formats for debugging

        audio_url = next((f.get('url') for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), None)
        if audio_url:
            song_queues[guild_id].append({'url': audio_url, 'title': data.get('title', 'Unknown')})
            if voice_clients[guild_id].is_playing():
                await message.channel.send("Added to queue!")
            else:
                player = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
                voice_clients[guild_id].play(
                    player,
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        play_next(guild_id), client.loop).result())
        else:
            await message.channel.send("Could not find a valid audio format.")
            logging.warning("No valid audio format found")

    @client.event  
    async def on_ready():
        logging.info(f'{client.user} is now connected and ready to play music!')

    @client.event  
    async def on_message(message):
        if message.content.startswith('?play'):
            try:
                if not message.author.voice:
                    await message.channel.send("You must join a voice channel first!")
                    return

                channel = message.author.voice.channel  
                if message.guild.id not in voice_clients:
                    voice_client = await channel.connect()
                    voice_clients[message.guild.id] = voice_client  
                    song_queues[message.guild.id] = deque()
                else:
                    voice_client = voice_clients[message.guild.id]

                if len(message.content.split()) > 1:
                    url = message.content.split()[1]
                else:
                    await message.channel.send("Please provide a URL to play.")
                    return

                loop = asyncio.get_event_loop()

                with yt_dlp.YoutubeDL(ytdl_options) as ydl:
                    try:
                        data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                        logging.info(f"Extracted data structure: {data}")
                    except yt_dlp.DownloadError as e:
                        error_msg = str(e)
                        if "This video is no longer available" in error_msg or "copyright claim" in error_msg:
                            await message.channel.send("This video is unavailable due to copyright restrictions.")
                        else:
                            await message.channel.send("An error occurred while trying to retrieve the video.")
                        logging.error(f"Error with URL {url}: {error_msg}")
                        return

                # Check for playlist or single track  
                if 'entries' in data and isinstance(data['entries'], list):
                    logging.info(f"Processing playlist with {len(data['entries'])} entries")
                    await message.channel.send(f"Adding {len(data['entries'])} songs to queue")

                    # Process each entry asynchronously  
                    tasks = []
                    for entry in data['entries']:
                        tasks.append(process_playlist_entry(entry, message.guild.id))

                    await asyncio.gather(*tasks)  # Run all tasks concurrently

                    if not voice_client.is_playing():
                        await play_next(message.guild.id)
                else:
                    await process_single_track(data, message.guild.id, message)

            except Exception as e:
                logging.error(f"Error processing command: {str(e)}")
                await message.channel.send("An error occurred while processing your request.")

    client.run(TOKEN)