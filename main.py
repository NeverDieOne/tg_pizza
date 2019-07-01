import json
import os
from dotenv import load_dotenv
import datetime
import requests
from slugify import slugify
from pprint import pprint


auth_data = None
token = None


def get_authorization_token():
    global token
    global auth_data
    if token is None:
        auth_data = get_authorization_data()
        token = auth_data[1]
    else:
        if is_token_valid(auth_data):
            token = auth_data[1]
        else:
            auth_data = get_authorization_data()
            token = auth_data[1]
    return token


def get_authorization_data():
    data = {
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'grant_type': 'client_credentials'
    }

    response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
    response.raise_for_status()
    response_json = response.json()

    return response_json['expires'], response_json['access_token']


def is_token_valid(auth_data):
    now = datetime.datetime.now()
    token_expires = datetime.datetime.fromtimestamp(auth_data[0])

    return now < token_expires


def create_product(product):
    token = get_authorization_token()
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    payload = {
        'type': 'product',
        'name': product['name'],
        'slug': slugify(product['name']),
        'sku': str(product['id']),
        'manage_stock': False,
        'description': product['description'],
        'price': [{
                    'amount': product['price'],
                    'currency': 'RUB',
                    'includes_tax': True
        }],
        'commodity_type': 'physical',
        'status': 'live'
    }
    response = requests.post(url, headers=headers, json={'data': payload})
    response.raise_for_status()

    return response.json()


def create_picture(product):
    pass


if __name__ == '__main__':
    load_dotenv()

    with open('addresses.json', 'r') as add_file:
        addresses = json.load(add_file)

    with open('menu.json', 'r') as menu_file:
        menu = json.load(menu_file)

    good = menu[0]
    print(create_product(good))
