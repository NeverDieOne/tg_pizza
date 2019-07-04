import redis
from dotenv import load_dotenv
import os


if __name__ == '__main__':
    load_dotenv()

    database_password = os.getenv("DATABASE_PASSWORD")
    database_host = os.getenv("DATABASE_HOST")
    database_port = os.getenv("DATABASE_PORT")
    database = redis.Redis(host=database_host, port=database_port, password=database_password)

    database.flushdb()
