import os
from dotenv import load_dotenv
import requests
from flask import Flask, request
from utils import generate_facebook_menu, genearage_facebook_main_cart, generate_facebook_categories_cart
from moltin import get_products_by_category_id, CATEGORIES
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
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                    message_text = messaging_event["message"]["text"]

                    handle_users_reply(sender_id, message_text)
    return "ok", 200


def handle_start(sender_id, message_text):
    params = {"access_token": FACEBOOK_TOKEN}
    headers = {"Content-Type": "application/json"}
    request_content = {
        "recipient": {
            "id": sender_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        genearage_facebook_main_cart(),
                        *generate_facebook_menu(get_products_by_category_id(CATEGORIES['prime'])),
                        generate_facebook_categories_cart()]
                }
            }
        }
    }
    response = requests.post(
        "https://graph.facebook.com/v2.6/me/messages",
        params=params, headers=headers, json=request_content
    )
    response.raise_for_status()
    return "START"


def handle_users_reply(sender_id, message_text):
    database = get_database_connection()
    states_functions = {
        'START': handle_start,
    }
    recorded_state = database.get(f'facebookid_{sender_id}')
    if not recorded_state or recorded_state.decode("utf-8") not in states_functions.keys():
        user_state = "START"
    else:
        user_state = recorded_state.decode("utf-8")
    if message_text == "/start":
        user_state = "START"
    state_handler = states_functions[user_state]
    next_state = state_handler(sender_id, message_text)
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
