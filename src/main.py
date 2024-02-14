import discord
import dotenv
import os
#from humblescraper import check_humble_bundle
import DevLinkCredits

dotenv.load_dotenv()
botToken = os.getenv('BOT_API_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

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
        
#check_humble_bundle(client)

client.run(botToken)