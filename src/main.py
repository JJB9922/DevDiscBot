import discord
import dotenv
import os
import constants
from uwuipy import uwuipy
from discord.ext import tasks
from humblescraper import run_humble_check, check_and_send_new_bundles

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
        await ctx.respond("🔄 Checking for new humble bundles...")
        try:
            await check_and_send_new_bundles(bot)
            await ctx.followup.send("✅ Humble bundle check completed!")
        except Exception as e:
            await ctx.followup.send(f"❌ Error: {str(e)}")
            print(f"Error in refreshhumble: {e}")
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
