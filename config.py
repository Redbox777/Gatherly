import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN      = os.environ.get("TOKEN", "8707826926:AAELSd4Ad7uMA8_YUtZuM5dof6OnTRqzB2Y")
DB_FILE    = os.environ.get("DB_FILE", "gatherly.db")
GROQ_KEY   = os.environ.get("GROQ_KEY", "")
YANDEX_KEY = os.environ.get("YANDEX_KEY", "")
