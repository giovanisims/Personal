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
    current_songs = {}

    ytdl_options = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,  # Ensures full info for each video  
        "noplaylist": False  # Explicitly set to handle playlists  
    }
    ytdl = yt_dlp.YoutubeDL(ytdl_options)
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -af "volume=0.5"'  # Added volume normalization  
    }

    async def play_next(guild_id):
        if song_queues[guild_id] and not voice_clients[guild_id].is_playing():
            try:
                song = song_queues[guild_id].popleft()
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(song['url'], download=False))
                
                if data:
                    url = data.get('url', song['url'])
                    player = discord.FFmpegPCMAudio(url, **ffmpeg_options)
                    voice_clients[guild_id].play(
                        player, 
                        after=lambda e: asyncio.run_coroutine_threadsafe(
                            play_next(guild_id), 
                            client.loop  
                        ).result()
                    )
            except Exception as e:
                logging.error(f"Error in play_next: {str(e)}")
                asyncio.run_coroutine_threadsafe(play_next(guild_id), client.loop)

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

                url = message.content.split()[1]
                loop = asyncio.get_event_loop()

                with yt_dlp.YoutubeDL(ytdl_options) as ydl:
                    data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                
                if 'entries' in data:  # It's a playlist  
                    logging.info(f"Processing playlist with {len(data['entries'])} entries")
                    await message.channel.send(f"Adding {len(data['entries'])} songs to queue")
                    for entry in data['entries']:
                        if entry and 'formats' in entry:
                            formats = entry['formats']
                            audio_url = next((f.get('url') for f in formats if f.get('acodec') != 'none'), None)
                            if audio_url:
                                song_queues[message.guild.id].append({'url': audio_url, 'title': entry.get('title', 'Unknown')})
                                logging.info(f"Added {entry.get('title', 'Unknown')} to queue")
                            else:
                                logging.warning(f"No audio format found for {entry.get('title', 'Unknown')}")
                    if not voice_client.is_playing():
                        await play_next(message.guild.id)
                else:  # Single track  
                    logging.info(f"Processing single track: {data.get('title', 'Unknown')}")
                    formats = data.get('formats', [])
                    audio_url = next((f.get('url') for f in formats if f.get('acodec') != 'none'), None)
                    if audio_url:
                        song_queues[message.guild.id].append({'url': audio_url, 'title': data.get('title', 'Unknown')})
                        if voice_client.is_playing():
                            await message.channel.send("Added to queue!")
                        else:
                            player = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
                            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(message.guild.id), client.loop).result())
                    else:
                        logging.warning("No valid audio format found")

            except Exception as e:
                logging.error(f"Error processing command: {str(e)}")
                await message.channel.send("An error occurred while processing your request.")

        elif message.content.startswith('?queue'):
            if message.guild.id in song_queues:
                queue_list = list(song_queues[message.guild.id])
                if queue_list:
                    queue_message = "\n".join(f"{idx+1}. {song['title']}" for idx, song in enumerate(queue_list))
                    await message.channel.send(f"Songs in queue:\n{queue_message}")
                else:
                    await message.channel.send("Queue is empty!")

        elif message.content.startswith('?shuffle'):
            if message.guild.id in song_queues and song_queues[message.guild.id]:
                random.shuffle(song_queues[message.guild.id])
                await message.channel.send("The queue has been shuffled!")
                logging.info("Shuffled the song queue")
            else:
                await message.channel.send("The queue is empty or does not exist!")

        elif message.content.startswith('?skip'):
            if message.guild.id in voice_clients:
                voice_clients[message.guild.id].stop()
                await play_next(message.guild.id)

        elif message.content.startswith('?pause') or message.content.startswith('?resume') or message.content.startswith('?stop'):
            try:
                if message.content.startswith('?pause'):
                    voice_clients[message.guild.id].pause()
                elif message.content.startswith('?resume'):
                    voice_clients[message.guild.id].resume()
                elif message.content.startswith('?stop'):
                    try:
                        if message.guild.id in voice_clients:
                            song_queues[message.guild.id].clear()  # Clear the queue  
                            await voice_clients[message.guild.id].disconnect()  # Disconnect from the voice channel  
                            del voice_clients[message.guild.id]  # Remove the voice client entry  
                            await message.channel.send("Playback stopped and disconnected from the voice channel.")
                    except Exception as e:
                        logging.error(f"Error handling stop command: {str(e)}")
            except Exception as e:
                logging.error(f"Error handling command: {str(e)}")

    client.run(TOKEN)