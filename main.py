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
    data = {
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
    response = requests.post(url, headers=headers, json={'data': data})
    response.raise_for_status()

    return response.json()['data']['id']


def download_picture(product):
    product_name = slugify(product['name'])
    filename = f"pictures/{product_name}.jpg"
    url = product['product_image']['url']

    response = requests.get(url)
    with open(filename, 'wb') as file:
        file.write(response.content)
    return file.name


def create_picture(picture):
    token = get_authorization_token()
    url = 'https://api.moltin.com/v2/files'
    # file = download_picture(product)
    headers = {
        'Authorization': f'Bearer {token}'
    }
    files = {
        'public': True,
        'file': open(picture, 'rb')
    }
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()

    return response.json()['data']['id']


def link_picture_to_product(product_id, picture_id):
    token = get_authorization_token()
    url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'type': 'main_image',
        'id': picture_id
    }
    response = requests.post(url, headers=headers, json={'data': data})
    response.raise_for_status()

    return response.json()


def load_products_to_shop(menu_file):
    with open(menu_file, 'r') as menu_file:
        menu = json.load(menu_file)

    for product in menu:
        picture = download_picture(product)

        product_id = create_product(product)
        picture_id = create_picture(picture)
        link_picture_to_product(product_id, picture_id)


def create_flow(name, description):
    token = get_authorization_token()
    url = 'https://api.moltin.com/v2/flows'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'type': 'flow',
        'name': name,
        'slug': slugify(name),
        'description': description,
        'enabled': True
    }
    response = requests.post(url, headers=headers, json={'data': data})
    response.raise_for_status()

    return response.json()


def create_field(name, description, flow_id):
    token = get_authorization_token()
    url = 'https://api.moltin.com/v2/fields'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'type': 'field',
        'name': name,
        'slug': slugify(name),
        'field_type': 'string',
        'description': description,
        'required': False,
        'unique': False,
        'default': '',
        'enabled': True,
        'relationships': {
            'flow': {
                'data': {
                    'type': 'flow',
                    'id': flow_id
                }
            }
        }
    }
    response = requests.post(url, headers=headers, json={'data': data})
    response.raise_for_status()

    return response.json()


def create_entry(flow_slug, shop):
    token = get_authorization_token()
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'type': 'entry',
        'address': shop['address']['full'],
        'alias': shop['alias'],
        'longitude': shop['coordinates']['lon'],
        'latitude': shop['coordinates']['lat']
    }
    response = requests.post(url, headers=headers, json={'data': data})
    response.raise_for_status()

    return response.json()


if __name__ == '__main__':
    load_dotenv()
