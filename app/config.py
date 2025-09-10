import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_DATABASE = os.getenv("YDB_DATABASE")
IMAGE_URL = "https://storage.yandexcloud.net/image-backet-chat-bot/anime_quiz_image.png"