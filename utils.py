import redis
import os

database = None


def get_database_connection():
    global database
    if not database:
        database = redis.Redis(
            host=os.getenv('DATABASE_HOST'),
            port=os.getenv('DATABASE_PORT'),
            db=os.getenv('DATABASE_NUMBER')
        )
    return database
