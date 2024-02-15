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

        embed = discord.Embed(description=f'**Bot Contributors: **\n{", ".join([f"<@{m}>" for m in DevLinkCredits.devList.values()])}', color=0xC3B1E1)
        await message.reply(embed=embed, mention_author=False)
        
#check_humble_bundle(client)

client.run(botToken)