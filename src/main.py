import discord
import dotenv
import os
import constants
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from uwuipy import uwuipy
from discord.ext import tasks


async def extract_json_data(session, url):
    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    script_tag = soup.find("script", id="landingPage-json-data")

    if not script_tag or not script_tag.contents:
        print("ERROR: Could not find landingPage-json-data script tag.")
        return None

    try:
        return json.loads(script_tag.contents[0].strip())
    except Exception as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        return None


def filter_books(json_data):
    if not json_data:
        return []

    data = json_data.get("data", {})
    books_data = data.get("books", {})
    mosaic_data = books_data.get("mosaic", [])

    if not mosaic_data:
        return []

    bundles_data = mosaic_data[0].get("products", [])

    filtered = []

    for product in bundles_data:
        tile_name = product.get("tile_name", "").lower()
        if any(keyword in tile_name for keyword in constants.humblekeywords):
            filtered.append({
                "title": tile_name,
                "description": product.get("short_marketing_blurb", ""),
                "url": product.get("product_url", ""),
                "image_url": product.get("tile_image", "")
            })

    return filtered


def load_books(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as f:
        return json.load(f)


def save_books(filename, books):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(books, f, indent=4)



dotenv.load_dotenv()
botToken = os.getenv("BOT_API_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # needed for roles

bot = discord.Bot(intents=intents)

# cache webhooks per channel
webhook_cache = {}


async def check_and_send_new_bundles():
    filename = "data/filtered_books.json"
    url = "https://www.humblebundle.com/books"

    async with aiohttp.ClientSession() as session:
        json_data = await extract_json_data(session, url)

    if not json_data:
        return

    new_books = filter_books(json_data)
    old_books = load_books(filename)

    difference = [b for b in new_books if b not in old_books]

    if not difference:
        return

    save_books(filename, new_books)

    for bundle in difference:
        await send_embed(bundle)


async def send_embed(embed_data):
    embed = discord.Embed(
        title=embed_data["title"].title(),
        description=embed_data["description"],
        color=0xBDFFBD
    )

    embed.add_field(
        name="Click Here to Buy",
        value=f"https://www.humblebundle.com{embed_data['url']}",
        inline=False
    )

    embed.set_image(url=embed_data["image_url"])

    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name="humble")
        if channel and channel.permissions_for(guild.me).send_messages:
            await channel.send(embed=embed)
            print(f"Sent embed to #{channel.name}")



@tasks.loop(hours=24)
async def check_daily_bundles():
    try:
        await check_and_send_new_bundles()
    except Exception as e:
        print(f"Bundle task failed: {e}")


@check_daily_bundles.before_loop
async def before_bundle_loop():
    await bot.wait_until_ready()



@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    if not check_daily_bundles.is_running():
        check_daily_bundles.start()


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild is None:
        return  # ignore DMs

    member = message.author

    if not isinstance(member, discord.Member):
        return

    if not any(role.name == "Forsaken..." for role in member.roles):
        return

    uwu = uwuipy(None, 0.3, 0.3, 0.3, 0.3, True)

    # reuse webhook instead of creating every time
    webhook = webhook_cache.get(message.channel.id)

    if not webhook:
        webhooks = await message.channel.webhooks()
        webhook = next((w for w in webhooks if w.name == "uwu-bot"), None)

        if not webhook:
            webhook = await message.channel.create_webhook(name="uwu-bot")

        webhook_cache[message.channel.id] = webhook

    await webhook.send(
        uwu.uwuify(message.content),
        username=member.display_name,
        avatar_url=member.display_avatar.url
    )

    await message.delete()

@bot.command(description="Ping the bot")
async def ping(ctx):
    await ctx.respond(f"Pong! {round(bot.latency * 1000)}ms")


@bot.command(description="Force refresh humble data")
async def refreshhumble(ctx):
    if ctx.author.id not in constants.devList.values():
        await ctx.respond("No permission.")
        return

    await ctx.respond("Running bundle check...")
    await check_and_send_new_bundles()
    await ctx.followup.send("Done.")


bot.run(botToken)
