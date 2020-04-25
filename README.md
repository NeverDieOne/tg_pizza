# Telegram Pizza Bot

Бот для отправки пиццы и приема платежей через Телеграм.

## Как установить

1. Клонировать репозиторий к себе
2. `pip install -r requirements.txt`
3. В корне папки создать файл `.env` и положить в него следующие переменные:
    * `CLIENT_ID` - ClientID от CMS Moltin
    * `CLIENT_SECRET` - Client Secret от CMS Moltin
    * `TG_TOKEN` - token вашего телеграмм бота
    * `API_KEY` - API key от Yandex Geocoder
    * `PAYMENT_TOKEN` - token вашей платежный системы для принятия платежей
    * `DATABASE_HOST` - host от DB Redis
    * `DATABASE_PORT` - port от DB Redis
    * `DATABASE_NUMBER` - номер DB Redis


## Пример запуска

```python tg_bot.py```

![Sample](https://media.giphy.com/media/gflsfushe82IkhcMQ9/giphy.gif)

## Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [Devman](https://dvmn.org/modules)