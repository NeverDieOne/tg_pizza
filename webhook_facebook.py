import os
from dotenv import load_dotenv
import requests
from flask import Flask, request
from utils import generate_facebook_menu, genearage_facebook_main_cart, generate_facebook_categories_cart, \
    send_facebook_message, generage_facebook_cart
from moltin import get_products_by_category_id, add_product_to_cart, get_products_in_cart, delete_product_from_basket, \
    get_or_create_cart
import redis

load_dotenv()

app = Flask(__name__)
FACEBOOK_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]

database = None


@app.route('/', methods=['GET'])
def verify():
    """
    При верификации вебхука у Facebook он отправит запрос на этот адрес. На него нужно ответить VERIFY_TOKEN.
    """
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():
    """
    Основной вебхук, на который будут приходить сообщения от Facebook.
    """
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]

                get_or_create_cart(sender_id)

                message_text = None
                postback_payload = None

                if messaging_event.get("message"):
                    message_text = messaging_event["message"]["text"]
                if messaging_event.get('postback'):
                    postback_payload = messaging_event["postback"]["payload"]

                handle_users_reply(sender_id,
                                   message_text=message_text,
                                   postback_payload=postback_payload)

    return "ok", 200


def handle_start(sender_id, message_text=None, postback_payload=None):
    if not postback_payload:
        postback_payload = '409e5b44-7e45-426b-bf26-7d1d14f8a6a5'

    if 'add' in postback_payload:
        product_id = postback_payload.split(', ')[-1]
        add_product_to_cart(cart_id=sender_id, product_id=product_id, product_amount=1)

        message = {
            'text': 'Товар успешно добавлен в корзину'
        }

        send_facebook_message(FACEBOOK_TOKEN, sender_id, message)

        return "START"

    if 'cart' in postback_payload:
        products = get_products_in_cart(sender_id)

        message = {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': [
                        *generage_facebook_cart(products)
                    ]
                }
            }
        }

        send_facebook_message(FACEBOOK_TOKEN, sender_id, message)

        return "MENU"

    message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    genearage_facebook_main_cart(),
                    *generate_facebook_menu(get_products_by_category_id(postback_payload)),
                    generate_facebook_categories_cart()]
            }
        }
    }

    send_facebook_message(FACEBOOK_TOKEN, sender_id, message)
    return "START"


def handle_menu(sender_id, message_text=None, postback_payload=None):
    if 'add' in postback_payload:
        product_id = postback_payload.split(', ')[-1]
        add_product_to_cart(cart_id=sender_id, product_id=product_id, product_amount=1)
        
        message = {
            'text': 'Товар успешно добавлен в корзину'
        }

        send_facebook_message(FACEBOOK_TOKEN, sender_id, message)

        return "MENU"

    if 'delete' in postback_payload:
        product_id = postback_payload.split(', ')[-1]
        delete_product_from_basket(sender_id, product_id)

        message = {
            'text': 'Товар успешно удален'
        }

        send_facebook_message(FACEBOOK_TOKEN, sender_id, message)

        return "MENU"

    if 'menu' in postback_payload:
        message = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        genearage_facebook_main_cart(),
                        *generate_facebook_menu(get_products_by_category_id('409e5b44-7e45-426b-bf26-7d1d14f8a6a5')),
                        generate_facebook_categories_cart()]
                }
            }
        }

        send_facebook_message(FACEBOOK_TOKEN, sender_id, message)
        return "START"


def handle_users_reply(sender_id, message_text=None, postback_payload=None):
    database = get_database_connection()
    states_functions = {
        'START': handle_start,
        'MENU': handle_menu
    }
    recorded_state = database.get(f'facebookid_{sender_id}')
    if not recorded_state or recorded_state.decode("utf-8") not in states_functions.keys():
        user_state = "START"
    else:
        user_state = recorded_state.decode("utf-8")
    if message_text == "/start":
        user_state = "START"
    state_handler = states_functions[user_state]
    next_state = state_handler(sender_id, message_text, postback_payload)
    database.set(f'facebookid_{sender_id}', next_state)


def get_database_connection():
    global database
    if database is None:
        database = redis.Redis(
            host=os.getenv('DATABASE_HOST'),
            port=os.getenv('DATABASE_PORT'),
            db=os.getenv('DATABASE_NUMBER')
        )
    return database


if __name__ == '__main__':
    app.run(debug=True)
