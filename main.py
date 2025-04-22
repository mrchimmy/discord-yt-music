# Python 3.10

import discord
from discord.ext import commands
import yt_dlp
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'nocheckcertificate': True
}

ffmpeg_options = {
    'options': '-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def bot_print(ctx, members: commands.Greedy[discord.Member], *, message):
    slapped = ", ".join(x.name for x in members)
    await ctx.send(f'{slapped} {message}')

@bot.command()
async def play(ctx, url):
    # ctx.author = คนเรียกคำสั่ง
    if ctx.author.voice: 
        
        if ctx.voice_client is None: # ctx.voice_client เช็คว่า bot เชื่อมต่อในห้องไหม
            await ctx.author.voice.channel.connect()
        elif ctx.voice_client.channel != ctx.author.voice.channel: # ถ้า channel ที่อยู่ไม่เหมือนกับคนเรียกคำสั่ง
            await ctx.voice_client.move_to(ctx.author.voice.channel)
    else:
        await ctx.send("คุณต้องอยู่ใน voice channel ก่อน")
        return

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.stop()
        ctx.voice_client.play(player, after=lambda e: print(f'Error: {e}') if e else None)
    await ctx.send(f'🎶 กำลังเล่น: {player.title}')

@bot.command()
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ พักเพลงแล้ว")

@bot.command()
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ เล่นเพลงต่อแล้ว")

@bot.command()
async def stop(ctx):
    ctx.voice_client.stop()
    await ctx.send("⏹️ หยุดเพลงแล้ว")

@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()
    await ctx.send("👋 ออกจากห้องแล้ว")

bot.run(BOT_TOKEN)
