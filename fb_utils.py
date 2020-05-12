import moltin
import requests


def genearate_facebook_main_cart():
    return {'title': 'Меню',
            'subtitle': 'Здесь вы можете выбрать один из вариантов',
            'image_url': 'https://image.freepik.com/free-vector/_15146-192.jpg',
            'buttons': [
                {'type': 'postback', 'title': 'Корзина', 'payload': 'cart'},
                {'type': 'postback', 'title': 'Акции', 'payload': 'stocks'},
                {'type': 'postback', 'title': 'Сделать заказ', 'payload': 'order'},
            ]}


def generate_facebook_menu(products_list=None) -> list:
    if not products_list:
        products_list = moltin.get_products()
    prodcuts = []

    for product in products_list:
        product_name = product["name"]
        product_description = product["description"]
        product_price = product["price"][0]["amount"]
        product_id = product["id"]

        photo_id = product["relationships"]["main_image"]["data"]["id"]
        product_photo_url = moltin.get_photo_url_by_id(photo_id)

        prodcuts.append({
            "title": f'{product_name} ({product_price} руб.)',
            "subtitle": product_description,
            "image_url": product_photo_url,
            "buttons": [
                {"type": "postback", "title": "Добавить в корзину", "payload": f"add, {product_id}"},
            ]
        })

    return prodcuts


def generate_facebook_categories_cart():
    return {'title': 'Не нашли нужную пиццу?',
            'subtitle': 'Остальные пиццы можно посмотреть в одной из категорий',
            'image_url': 'https://primepizza.ru/uploads/position/large_0c07c6fd5c4dcadddaf4a2f1a2c218760b20c396.jpg',
            'buttons': [
                {'type': 'postback', 'title': 'Острые', 'payload': '0cd20248-9e23-4304-9c38-04f547276001'},
                {'type': 'postback', 'title': 'Сытные', 'payload': 'c1af2f67-634f-4b46-b790-8e3ae5dcbae7'},
                {'type': 'postback', 'title': 'Особые', 'payload': '32002b43-1136-4b6d-9f6d-f77bf424ac1a'},
            ]}


def send_facebook_message(facebook_token, sender_id, message):
    params = {"access_token": facebook_token}
    headers = {"Content-Type": "application/json"}

    request_content = {
        'recipient': {
            'id': sender_id
        },
        'message': message
    }
    response = requests.post(
        "https://graph.facebook.com/v2.6/me/messages",
        params=params, headers=headers, json=request_content
    )
    response.raise_for_status()


def generage_facebook_cart(products_list):
    total = sum([product['meta']['display_price']['with_tax']['value']['amount'] for product in products_list])

    cards = [{
        'title': f'Заказ на сумму {total}',
        'image_url': 'https://postium.ru/wp-content/uploads/2018/08/idealnaya-korzina-internet-magazina-1068x713.jpg',
        'buttons': [
            {"type": "postback", "title": "Самовывоз", "payload": "pickup"},
            {"type": "postback", "title": "Доставка", "payload": "delivery"},
            {"type": "postback", "title": "К меню", "payload": "menu"},
        ]
    }]

    for product in products_list:
        product_id = product['product_id']
        delete_id = product['id']
        product_name = product['name']
        product_description = product['description']
        numbers = product['quantity']

        photo_url = product['image']['href']

        cards.append({
            "title": f'{product_name} x {numbers}',
            "subtitle": product_description,
            "image_url": photo_url,
            "buttons": [
                {"type": "postback", "title": "Добавить еще одну", "payload": f"add, {product_id}"},
                {"type": "postback", "title": "Удалить из корзины", "payload": f"delete, {delete_id}"},
            ]
        })

    return cards
