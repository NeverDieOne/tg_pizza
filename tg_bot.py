import os
import logging
import redis
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import moltin
import utils

database = None


def start(bot, update):
    goods = moltin.get_goods()

    moltin.get_or_create_cart(update.message.chat_id)

    keyboard = [[InlineKeyboardButton(good['name'], callback_data=good['id'])] for good in goods]
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text='Please choose:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update):
    query = update.callback_query

    if query.data == 'cart':
        utils.show_cart(query, bot, update)
        return "HANDLE_CART"
    else:
        keyboard = [[InlineKeyboardButton('1 кг', callback_data=f'1kg, {query.data}'),
                     InlineKeyboardButton('5 кг', callback_data=f'5kg, {query.data}'),
                     InlineKeyboardButton('10 кг', callback_data=f'10kg, {query.data}')],
                    [InlineKeyboardButton('Назад', callback_data='back')],
                    [InlineKeyboardButton('Корзина', callback_data='cart')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        good_info = moltin.get_item_by_id(query.data)
        good_photo_id = good_info['relationships']['main_image']['data']['id']
        good_photo = moltin.get_photo_url_by_id(good_photo_id)

        name = good_info['name']
        description = good_info['description']
        price_per_kg = f"{good_info['meta']['display_price']['with_tax']['formatted']} per kg"
        if good_info['meta']['stock']['availability'] == 'in-stock':
            on_stock_kg = f"{good_info['meta']['stock']['level']} on stock"
        else:
            on_stock_kg = 'Товара нет в наличии'

        bot.send_photo(chat_id=query.message.chat_id,
                       photo=good_photo,
                       caption=f"{name}\n\n{price_per_kg}\n{on_stock_kg}\n\n{description}",
                       reply_markup=reply_markup)
        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)
        return "HANDLE_DESCRIPTION"


def handle_description(bot, update):
    query = update.callback_query
    info = query.data.split(', ')

    if info[0] == 'back':
        goods = moltin.get_goods()
        keyboard = [[InlineKeyboardButton(good['name'], callback_data=good['id'])] for good in goods]
        keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        #  Если здесь использовать edit_message_text, то будет ошибка: 'NoneType' object has no attribute 'reply_text'
        #  т.к. в описании картинки не text, а caption
        bot.send_message(text='Please choose:',
                         reply_markup=reply_markup,
                         chat_id=query.message.chat_id)
        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)
        return "HANDLE_MENU"

    elif info[0] == 'cart':
        utils.show_cart(query, bot, update)
        return "HANDLE_CART"
    elif info[0] == '1kg':
        moltin.add_product_to_cart(cart_id=query.message.chat_id,
                                   product_id=info[1],
                                   product_amount=1)
    elif info[0] == '5kg':
        moltin.add_product_to_cart(cart_id=query.message.chat_id,
                                   product_id=info[1],
                                   product_amount=5)
    elif info[0] == '10kg':
        moltin.add_product_to_cart(cart_id=query.message.chat_id,
                                   product_id=info[1],
                                   product_amount=10)


def handle_cart(bot, update):
    query = update.callback_query

    if query.data == 'menu':
        goods = moltin.get_goods()
        keyboard = [[InlineKeyboardButton(good['name'], callback_data=good['id'])] for good in goods]
        keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        bot.edit_message_text(text='Please choose:',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=reply_markup)
        return "HANDLE_MENU"
    elif query.data == 'payment':
        bot.edit_message_text(text='Введите телефон для связи',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        return "WAITING_PHONE_NUMBER"
    else:
        moltin.delete_item_from_basket(query.message.chat_id, query.data)
        utils.show_cart(query, bot, update)
        return "HANDLE_CART"


def handle_phone_number(bot, update):
    first_name = update['message']['chat']['first_name']
    last_name = update['message']['chat']['last_name']
    phone = update.message.text

    moltin.create_customer(first_name, last_name, phone)
    bot.send_message(text=f'Вы прислали мне этот номер: {phone}\nС вами скоро свяжуться',
                     chat_id=update.message.chat_id)


def handle_users_reply(bot, update):
    database = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = database.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_PHONE_NUMBER': handle_phone_number
    }
    state_handler = states_functions[user_state]
    next_state = state_handler(bot, update)
    database.set(chat_id, next_state)


def get_database_connection():
    global database
    if database is None:
        database_password = os.getenv("DATABASE_PASSWORD")
        database_host = os.getenv("DATABASE_HOST")
        database_port = os.getenv("DATABASE_PORT")
        database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return database


def error_callback(bot, update, error):
    try:
        logging.error(str(update))
        update.message.reply_text(text='Простите, возникла ошибка.')
    except Exception as err:
        logging.critical(err)


if __name__ == '__main__':
    load_dotenv()

    token = os.getenv("TG_TOKEN")
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    dispatcher.add_error_handler(error_callback)
    updater.start_polling()