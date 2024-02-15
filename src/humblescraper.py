import json
import os
import requests
import discord
import constants
from bs4 import BeautifulSoup

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
    await bot.get_channel(1207442996161814578).send(embed=embed)

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
