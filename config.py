import os
from dotenv import load_dotenv

# Загрузка переменных из .env, если файл существует
load_dotenv()

# Проверяем, запущено ли приложение на Render
is_render = os.getenv("RENDER") is not None

# Считываем переменные окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
FLASK_SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")

# Проверка на наличие ключей
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не найден. Убедитесь, что переменная окружения настроена.")
if not ASSISTANT_ID:
    raise ValueError("ASSISTANT_ID не найден. Убедитесь, что переменная окружения настроена.")

# Настройки клиента OpenAI
openai_client_settings = {
    "api_key": OPENAI_API_KEY,
}
