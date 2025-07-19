import discord
import dotenv
import os
import constants
import json
import requests
from bs4 import BeautifulSoup
from uwuipy import uwuipy
from discord.ext import tasks

def extract_json_data(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    script_tag = soup.find('script', id='landingPage-json-data')
    json_data = json.loads(script_tag.contents[0].strip())

    return json_data

def filter_and_save_books_with_keywords_to_file(json_data, filename):
    data = json_data.get('data', {})
    books_data = data.get('books', [])
    mosaic_data = books_data.get('mosaic', [])
    bundles_data = mosaic_data[0].get('products', [])

    filtered_books = []

    for product in bundles_data:
        tile_name = product.get('tile_name', '').lower()
        short_marketing_blurb = product.get('short_marketing_blurb', '')
        product_url = product.get('product_url', '')
        image_url = product.get('tile_image', '')

        if any(keyword in tile_name for keyword in constants.humblekeywords):
            filtered_books.append({
                'title': tile_name,
                'description': short_marketing_blurb,
                'url': product_url,
                'image_url': image_url
            })

    with open(filename, 'w') as file:
        json.dump(filtered_books, file, indent=4, sort_keys=True)

def load_books_from_file(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def run_humble_check():
    url = 'https://www.humblebundle.com/books'
    json_data = extract_json_data(url)
    filename = 'data/filtered_books.json'
    filter_and_save_books_with_keywords_to_file(json_data, filename)
    print('Latest humble bundle data saved to file')

async def send_humble_embed(embed_data, bot):
    embed = discord.Embed(
        title=embed_data['title'].title(),
        description=embed_data['description'],
        color=0xBDFFBD
    )
    embed.add_field(name="Click Here to Buy", value=f"https://www.humblebundle.com{embed_data['url']}", inline=False)
    embed.set_image(url=embed_data['image_url'])
    
    channel = discord.utils.get(bot.get_all_channels(), name="humble")
    if channel:
        await channel.send(embed=embed)
        print(f"Sent embed to #{channel.name}")
    else:
        print("ERROR: Could not find #humble channel!")
        for guild in bot.guilds:
            for text_channel in guild.text_channels:
                if text_channel.permissions_for(guild.me).send_messages:
                    await text_channel.send(f"**Humble Bundle Alert** (couldn't find #humble channel):")
                    await text_channel.send(embed=embed)
                    print(f"Sent to fallback channel: #{text_channel.name}")
                    return

async def check_and_send_new_bundles(bot):
    filename = 'data/filtered_books.json'

    if not os.path.exists(filename):
        with open(filename, 'w') as file:
            file.write('[]')

    current_books = load_books_from_file(filename)
    run_humble_check()
    new_books = load_books_from_file(filename)

    difference_books = [book for book in new_books if book not in current_books]

    for bundle in difference_books:
        await send_humble_embed(bundle, bot)

dotenv.load_dotenv()
botToken = os.getenv('BOT_API_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print("Starting daily bundle checker...")
    check_daily_bundles.start()

@bot.command(description="Ping the bot to check if it's online")
async def ping(ctx):
    await ctx.respond(f'Pong! {round(bot.latency * 1000)}ms')
        
@bot.command(description="List the bot contributors")
async def makers(ctx):
    newline = '\n'
    embed = discord.Embed(description=f'**Bot Contributors: **\n{"".join([f"<@{m}>{newline}" for m in constants.devList.values()])}', color=0xC3B1E1)
    await ctx.respond(embed=embed)
        
@bot.command(description="Refresh the humble bundle data")
async def refreshhumble(ctx):
    if ctx.author.id in constants.devList.values():
        await ctx.respond("🔄 Starting humble bundle check...")
        
        try:
            # Get current bundles count
            filename = 'data/filtered_books.json'
            if os.path.exists(filename):
                current_books = load_books_from_file(filename)
                current_count = len(current_books)
            else:
                current_count = 0
            
            await ctx.followup.send(f"📚 Current bundles in database: {current_count}")
            
            # Run the check
            await check_and_send_new_bundles(bot)
            
            # Get new count
            new_books = load_books_from_file(filename)
            new_count = len(new_books)
            difference = new_count - current_count
            
            if difference > 0:
                await ctx.followup.send(f"🎉 Found {difference} new bundle(s)! Total: {new_count}")
            else:
                await ctx.followup.send(f"ℹ️ No new bundles found. Total: {new_count}")
                
        except Exception as e:
            await ctx.followup.send(f"❌ Error occurred: {str(e)}")
            print(f"Error in refreshhumbledetailed: {e}")
    else:
        await ctx.respond("❌ You don't have permission to use this command.")
        
@bot.command(description="Purge the chat of the last 10 messages")
async def clear(ctx):
    if ctx.author.id in constants.devList.values():
        await ctx.channel.purge(limit=10)
        
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if any(role.name == "Forsaken..." for role in message.author.roles):        
        uwu = uwuipy(None, 0.3, 0.3, 0.3, 0.3, True)
        webhook = await message.channel.create_webhook(name=message.author.display_name)
        await webhook.send(f'{uwu.uwuify(message.content)}', username=message.author.display_name, avatar_url=message.author.avatar.url)
        await webhook.delete()
        await message.delete()


@tasks.loop(hours=24)
async def check_daily_bundles():
    await check_and_send_new_bundles(bot)

bot.run(botToken)
