import os
import sys
from dotenv import load_dotenv

# Определение, находимся ли мы в среде Render
is_render = os.environ.get('RENDER') == 'true'

# Загрузка переменных окружения из .env файла (только если мы не на Render)
if not is_render:
    print("Локальная среда: Загрузка переменных из .env файла")
    if not os.path.exists('.env') and os.path.exists('.env.example'):
        print("ВНИМАНИЕ: Файл .env не найден. Создаем копию из .env.example")
        with open('.env.example', 'r') as example_file:
            with open('.env', 'w') as env_file:
                env_file.write(example_file.read())
    
    load_dotenv()
else:
    print("Среда Render: Используются системные переменные окружения")

# Загрузка конфигурационных параметров
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_ORG_ID = os.getenv('OPENAI_ORG_ID', '')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-123')
DIALOGUES_FILE = "storage/dialogues.json"
KNOWLEDGEBASE_DIR = os.getenv("KNOWLEDGEBASE_DIR", "storage/knowledgebase")

# Проверка наличия необходимых переменных и вывод отладочной информации
if not OPENAI_API_KEY:
    print("ВНИМАНИЕ: OPENAI_API_KEY не найден в переменных окружения")
else:
    print(f"Тип API ключа: {'Ключ проекта' if OPENAI_API_KEY.startswith('sk-proj-') else 'Обычный ключ'}")
    print(f"Первые 10 символов ключа: {OPENAI_API_KEY[:10]}***")

if OPENAI_ORG_ID:
    print(f"ID организации настроен: {OPENAI_ORG_ID[:4]}***")

if not ASSISTANT_ID:
    print("ВНИМАНИЕ: ASSISTANT_ID не найден в переменных окружения")
else:
    print(f"ID ассистента: {ASSISTANT_ID[:10]}***")
    
# Настройки для создания клиента OpenAI
openai_client_settings = {
    "api_key": OPENAI_API_KEY,
}

if OPENAI_ORG_ID:
    openai_client_settings["organization"] = OPENAI_ORG_ID
