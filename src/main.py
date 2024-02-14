import discord
import dotenv
import os
import DevLinkCredits
import requests
from bs4 import BeautifulSoup
import discord
import json
from humblescraper import run_humble_check, check_and_send_new_bundles
import asyncio

dotenv.load_dotenv()
botToken = os.getenv('BOT_API_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    print("Starting daily bundle checker...")
    await check_daily_bundles(client);

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('d.ping'):
        await message.channel.send(f'Pong! {round(client.latency * 1000)}ms')
        
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('d.makers'):
        await message.channel.send("My makers are:\n")
        for member in DevLinkCredits.devList:
            await message.channel.send(f'<@{DevLinkCredits.devList[member]}>\n')

@client.event
async def on_message(message):
    if message.author == client.user: 
        return

    if message.content.startswith('d.humble') and message.author.id in DevLinkCredits.devList.values():
        await check_and_send_new_bundles(client)  
        
async def check_daily_bundles(client):
    while True:
        await check_and_send_new_bundles(client)
        await asyncio.sleep(24 * 3600) 
        
client.run(botToken)