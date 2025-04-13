import os
import sys
from dotenv import load_dotenv

# Определение, находимся ли мы в среде Render
is_render = os.environ.get('RENDER') == 'true'

# Основной приоритет - всегда использовать переменные среды из системы
# Если они не заполнены, тогда использовать .env файл
print(f"Определена среда: {'Render' if is_render else 'Локальная'}")

# Даже в среде Render загрузим .env файл как запасной вариант
if os.path.exists('.env'):
    print("Загрузка переменных из .env файла")
    load_dotenv(override=False)  # Не перезаписываем системные переменные
elif os.path.exists('.env.example') and not is_render:
    print("ВНИМАНИЕ: Файл .env не найден. Создаем копию из .env.example")
    with open('.env.example', 'r') as example_file:
        with open('.env', 'w') as env_file:
            env_file.write(example_file.read())
    load_dotenv(override=False)

# Ручное добавление переменных Render в окружение (обходной путь для решения проблемы)
# Эта часть важна, так как некоторые версии dotenv и Render могут иметь проблемы совместимости
if is_render:
    # Проверка конкретных переменных в журналах Render
    print("Проверка настроек переменных окружения Render...")
    render_env_file = '/etc/secrets/env'
    if os.path.exists(render_env_file):
        print(f"Найден файл переменных Render: {render_env_file}")
        with open(render_env_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    if not os.environ.get(key):
                        os.environ[key] = value
                        print(f"Добавлена переменная из Render: {key}")

# Загрузка конфигурационных параметров
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
OPENAI_ORG_ID = os.environ.get('OPENAI_ORG_ID') or os.getenv('OPENAI_ORG_ID', '')
ASSISTANT_ID = os.environ.get('ASSISTANT_ID') or os.getenv('ASSISTANT_ID')
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or os.getenv('FLASK_SECRET_KEY', 'default-secret-key-123')
DIALOGUES_FILE = "storage/dialogues.json"
KNOWLEDGEBASE_DIR = os.getenv("KNOWLEDGEBASE_DIR", "storage/knowledgebase")

# Расширенная диагностика для поиска проблемы с переменными
print("\n=== Диагностика переменных окружения ===")
if not OPENAI_API_KEY:
    print("КРИТИЧЕСКАЯ ОШИБКА: OPENAI_API_KEY не найден в переменных окружения")
else:
    print(f"Тип API ключа: {'Ключ проекта' if OPENAI_API_KEY.startswith('sk-proj-') else 'Обычный ключ'}")
    print(f"Длина ключа: {len(OPENAI_API_KEY)} символов")
    print(f"Первые 10 символов: {OPENAI_API_KEY[:10]}***")
    print(f"Последние 5 символов: ***{OPENAI_API_KEY[-5:]}")

if not ASSISTANT_ID:
    print("КРИТИЧЕСКАЯ ОШИБКА: ASSISTANT_ID не найден в переменных окружения")
else:
    print(f"ID ассистента: {ASSISTANT_ID}")

if OPENAI_ORG_ID:
    print(f"ID организации настроен: {OPENAI_ORG_ID}")
    
# Настройки для создания клиента OpenAI
openai_client_settings = {
    "api_key": OPENAI_API_KEY,
}

if OPENAI_ORG_ID:
    openai_client_settings["organization"] = OPENAI_ORG_ID

print("=== Конец диагностики переменных ===\n")
