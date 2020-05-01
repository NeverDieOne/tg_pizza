import moltin
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import math
from geopy.distance import distance
import json
from dotenv import load_dotenv

load_dotenv()


def show_cart(query, bot, update):
    goods = moltin.get_products_in_cart(query.message.chat_id)

    list_reply = []
    total = sum([good['meta']['display_price']['with_tax']['value']['amount'] for good in goods])
    for good in goods:
        name = good['name']
        description = good['description']
        numbers = good['quantity']

        price = good['meta']['display_price']['with_tax']
        total_price = price['value']['formatted']
        list_reply.append(f"{name}\n{description}\n{numbers} пицц(а) в корзине на сумму {total_price} руб.\n\n")
    list_reply.append(f'К оплате: {total} руб.')
    reply = ''.join(list_reply)

    keyboard = [[InlineKeyboardButton(f"Удалить товар {good['name']}", callback_data=good['id'])] for good in goods]
    keyboard.append([InlineKeyboardButton('В меню', callback_data='menu')])
    keyboard.append([InlineKeyboardButton('Оплатить', callback_data=f'payment, {total}')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(text=reply,
                     reply_markup=reply_markup,
                     chat_id=query.message.chat_id)
    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)


def get_pagination(per_page):
    products = moltin.get_products()

    products_per_page = per_page
    max_page = math.ceil(len(products) / products_per_page)

    start = 0
    end = products_per_page

    paginated_goods = []

    for _ in range(max_page):
        paginated_goods.append(products[start: end])
        start = end
        end += products_per_page

    return paginated_goods


def create_menu_markup(page=0):
    products_per_page = 8
    products = get_pagination(products_per_page)
    keyboard = [[InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in products[page]]

    if page == len(products) - 1:
        keyboard.append([InlineKeyboardButton('Назад', callback_data=f'pag, {page - 1}')])
    elif page == 0:
        keyboard.append([InlineKeyboardButton('Вперед', callback_data=f'pag, {page + 1}')])
    else:
        keyboard.append([InlineKeyboardButton('Назад', callback_data=f'pag, {page - 1}'),
                         InlineKeyboardButton('Вперед', callback_data=f'pag, {page + 1}')])

    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


def min_dist(entry):
    return entry['distance']


def get_closest_entry(current_pos, entries):
    result = []

    for entry in entries:
        _id = entry['id']
        pos = entry['longitude'], entry['latitude']
        ent_tg = entry['telegram-id']
        ent_address = entry['address']

        _distance = distance(current_pos, pos).km

        result.append({'id': _id, 'distance': _distance, 'telegram-id': ent_tg, 'address': ent_address})

    return min(result, key=min_dist)


def create_delivery_menu(suplier, current_pos):
    data = [suplier, current_pos]
    data = json.dumps(data)

    keyboard = [[InlineKeyboardButton('Доставка', callback_data=f'{data}'),
                 InlineKeyboardButton('Самовывоз', callback_data='pickup')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup
