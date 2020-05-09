import time
import redis
import os
import requests
from dotenv import load_dotenv
from moltin import get_authorization_token, get_all_categories
import json

load_dotenv()
database = None


def get_database_connection():
    global database
    if database is None:
        database = redis.Redis(
            host=os.getenv('DATABASE_HOST'),
            port=os.getenv('DATABASE_PORT'),
            db=os.getenv('DATABASE_NUMBER')
        )
    return database


def create_menu(category_id):
    token = get_authorization_token()
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    params = {
        'filter': f'eq(category.id,{category_id})'
    }
    respone = requests.get(url, headers=headers, params=params)
    respone.raise_for_status()

    return respone.json()['data']


def cache_menu():
    database = get_database_connection()

    categories = [category['id'] for category in get_all_categories()]

    for category_id in categories:
        menu = create_menu(category_id)
        json_menu = json.dumps(menu)
        database.set(f"menu_{category_id}", json_menu)


if __name__ == '__main__':
    while True:
        cache_menu()
        time.sleep(60*5)
