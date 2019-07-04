import moltin
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from pprint import pprint


def show_cart(query, bot, update):
    goods = moltin.get_items_in_cart(query.message.chat_id)

    list_reply = []
    total = sum([good['meta']['display_price']['with_tax']['value']['amount'] for good in goods])
    for good in goods:
        name = good['name']
        description = good['description']
        numbers = good['quantity']

        price = good['meta']['display_price']['with_tax']
        total_price = price['value']['formatted']
        list_reply.append(f"{name}\n{description}\n{numbers} пицц(а) в корзине на сумму {total_price}\n\n")
    list_reply.append(f'К оплате: {total} руб.')
    reply = ''.join(list_reply)

    keyboard = [[InlineKeyboardButton(f"Удалить товар {good['name']}", callback_data=good['id'])] for good in goods]
    keyboard.append([InlineKeyboardButton('В меню', callback_data='menu')])
    keyboard.append([InlineKeyboardButton('Оплатить', callback_data='payment')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(text=reply,
                     reply_markup=reply_markup,
                     chat_id=query.message.chat_id)
    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)
