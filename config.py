import os
from dotenv import load_dotenv
import sys

# Определение, находимся ли мы в среде Render
is_render = os.environ.get('RENDER') == 'true'

# Загрузка переменных окружения из .env файла (только если мы не на Render)
# На Render переменные окружения устанавливаются через панель управления
if not is_render:
    print("Локальная среда: Загрузка переменных из .env файла")
    # Если нет файла .env, но есть .env.example, создаем .env из примера
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
OPENAI_ORG_ID = os.getenv('OPENAI_ORG_ID', '')  # Добавляем поддержку ID организации
ASSISTANT_ID = os.getenv('ASSISTANT_ID')
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-123')
DIALOGUES_FILE = "storage/dialogues.json"
KNOWLEDGEBASE_DIR = os.getenv("KNOWLEDGEBASE_DIR", "storage/knowledgebase")

# Проверка наличия необходимых переменных
if not OPENAI_API_KEY:
    print("ВНИМАНИЕ: OPENAI_API_KEY не найден в переменных окружения")
    if is_render:
        print("На Render необходимо настроить OPENAI_API_KEY в настройках сервиса")
    else:
        print("Убедитесь, что ваш .env файл содержит OPENAI_API_KEY")
        
if not ASSISTANT_ID:
    print("ВНИМАНИЕ: ASSISTANT_ID не найден в переменных окружения")
    if is_render:
        print("На Render необходимо настроить ASSISTANT_ID в настройках сервиса")
    else:
        print("Убедитесь, что ваш .env файл содержит ASSISTANT_ID")
