import os
from dotenv import load_dotenv

# Загрузка переменных из .env, если файл существует
load_dotenv()

# Проверяем, запущено ли приложение на Render
is_render = os.getenv("RENDER") is not None

# Считываем переменные окружения
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
DIALOGUES_FILE = os.getenv("DIALOGUES_FILE", "storage/dialogues.json")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "your-default-secret-key")
KNOWLEDGEBASE_DIR = os.getenv("KNOWLEDGEBASE_DIR", "storage/knowledgebase")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверка на наличие ключей
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не найден. Убедитесь, что переменная окружения настроена.")
if not ASSISTANT_ID:
    raise ValueError("ASSISTANT_ID не найден. Убедитесь, что переменная окружения настроена.")
if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError("ADMIN_USERNAME и ADMIN_PASSWORD должны быть настроены.")

# Настройки клиента OpenAI
openai_client_settings = {
    "api_key": OPENAI_API_KEY,
}
