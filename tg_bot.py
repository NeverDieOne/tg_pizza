import os
import logging
import redis
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import moltin
import utils
from yandex_geocoder import Client, exceptions
import json

database = None


def start(bot, update):
    moltin.get_or_create_cart(update.message.chat_id)

    reply_markup = utils.create_menu_markup()

    update.message.reply_text(text='Выберите товар:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update):
    query = update.callback_query

    if query.data == 'cart':
        utils.show_cart(query, bot, update)
        return "HANDLE_CART"
    elif 'pag' in query.data:
        page = query.data.split(', ')[1]
        reply_markup = utils.create_menu_markup(int(page))

        bot.edit_message_text(text='Выберите товар:',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton('Положить в корзину', callback_data=f'add, {query.data}')],
                    [InlineKeyboardButton('Назад', callback_data='back')],
                    [InlineKeyboardButton('Корзина', callback_data='cart')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        good_info = moltin.get_item_by_id(query.data)
        good_photo_id = good_info['relationships']['main_image']['data']['id']
        good_photo = moltin.get_photo_url_by_id(good_photo_id)

        name = good_info['name']
        description = good_info['description']
        price = good_info['price'][0]['amount']

        bot.send_photo(chat_id=query.message.chat_id,
                       photo=good_photo,
                       caption=f"{name}\nСтоимость: {price} руб.\n\n{description}",
                       reply_markup=reply_markup)
        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)
        return "HANDLE_DESCRIPTION"


def handle_description(bot, update):
    query = update.callback_query
    info = query.data.split(', ')

    if info[0] == 'back':
        reply_markup = utils.create_menu_markup()

        #  Если здесь использовать edit_message_text, то будет ошибка: 'NoneType' object has no attribute 'reply_text'
        #  т.к. в описании картинки не text, а caption
        bot.send_message(text='Выберите товар:',
                         reply_markup=reply_markup,
                         chat_id=query.message.chat_id)
        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)
        return "HANDLE_MENU"

    elif info[0] == 'cart':
        utils.show_cart(query, bot, update)
        return "HANDLE_CART"
    elif info[0] == 'add':
        moltin.add_product_to_cart(cart_id=query.message.chat_id,
                                   product_id=info[1],
                                   product_amount=1)


def handle_cart(bot, update):
    query = update.callback_query

    if query.data == 'menu':
        reply_markup = utils.create_menu_markup()

        bot.edit_message_text(text='Выберите товар:',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=reply_markup)
        return "HANDLE_MENU"
    elif query.data == 'payment':
        bot.edit_message_text(text='Пришлите нам Ваш адрес текстом или геолокацию.',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        return "HANDLE_WAITING"
    else:
        moltin.delete_item_from_basket(query.message.chat_id, query.data)
        utils.show_cart(query, bot, update)
        return "HANDLE_CART"


def handle_waiting(bot, update):
    if update.message.text:
        try:
            current_pos = Client.coordinates(update.message.text)  # Адрес возвращается (str, str)
        except exceptions.YandexGeocoderAddressNotFound:
            current_pos = None
            bot.send_message(text='Не могу распознать этот адрес',
                             chat_id=update.message.chat_id)
    else:
        message = None
        if update.edited_message:
            message = update.edited_message
        else:
            message = update.message
        current_pos = (message.location.longitude, message.location.latitude)  # Адрес возвращается (float, float)

    if current_pos:
        flow_slug = 'pizzeria'

        moltin.create_customer_address(current_pos, update.message.chat_id)

        entries = moltin.get_entries(flow_slug)
        closest_entry = utils.get_closest_entry(current_pos, entries)
        entry = moltin.get_entry(flow_slug, closest_entry['id'])

        supplier = entry['telegram-id']

        _distance = round(closest_entry["distance"], 1)

        if closest_entry['distance'] < 0.5:
            reply = f'Может, заребере пиццу из нашей пиццерии неподалеку? Она всего в {_distance} км от Вас! ' \
                f'Вот ее адрес: {entry["address"]}\n\nА можем и бесплатно доставить, нам не сложно c:'
            reply_markup = utils.create_delivery_menu(supplier, current_pos)
        elif closest_entry['distance'] < 5:
            reply = f'Похоже, придется ехать до Вас на самокате. ' \
                f'Доставка будет стоить 100 рублей. Доставляем или самовывоз?'
            reply_markup = utils.create_delivery_menu(supplier, current_pos)
        elif closest_entry['distance'] < 20:
            reply = f'А Вы не так близки к нам :c Доставка будет стоить 300 рублей.'
            reply_markup = utils.create_delivery_menu(supplier, current_pos)
        else:
            reply = f'Простите, но так далеко пиццу не доставим. Ближайшая пиццерия аж в {_distance} км от Вас!'
            reply_markup = None
            bot.send_message(text=reply,
                             chat_id=update.message.chat_id)

        if reply_markup:
            bot.send_message(text=reply,
                             chat_id=update.message.chat_id,
                             reply_markup=reply_markup)

            return "HANDLE_DELIVERY"


def handle_delivery(bot, update):
    query = update.callback_query

    try:
        data = json.loads(query.data)
    except:
        pass

    if query.data == 'pickup':
        print('pickup')
    elif data:
        id_tg = data[0]
        pos = data[1]
        bot.send_location(
            chat_id=id_tg,
            longitude=pos[0],
            latitude=pos[1]
        )


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
        'HANDLE_WAITING': handle_waiting,
        'HANDLE_DELIVERY': handle_delivery
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
    dispatcher.add_handler(MessageHandler(Filters.location, handle_waiting, edited_updates=True))
    dispatcher.add_error_handler(error_callback)
    updater.start_polling()
