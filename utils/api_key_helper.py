"""
API Key Helper - утилита для проверки и форматирования ключей OpenAI API
"""

import os
import re
import sys
import json
from pathlib import Path

def validate_openai_key(key):
    """
    Проверяет, что ключ API имеет правильный формат.
    
    Возвращает:
    - True если ключ имеет правильный формат
    - False в противном случае
    """
    if not key:
        return False
    
    # Проверка для стандартных ключей API (sk-...)
    if key.startswith('sk-') and len(key) > 20:
        return True
    
    # Проверка для ключей проекта (sk-proj-...)
    if key.startswith('sk-proj-') and len(key) > 30:
        return True
    
    return False

def fix_key_format(key):
    """
    Исправляет распространенные проблемы с форматом ключа API.
    
    Возвращает:
    - Исправленный ключ или None, если ключ невозможно исправить
    """
    if not key:
        return None
        
    # Удаляем лишние пробелы и символы новой строки
    key = key.strip()
    
    # Иногда ключи копируются с кавычками
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1]
    
    # Иногда в окружении ключи сохраняются с лишними символами
    key = re.sub(r'[^a-zA-Z0-9_\-]', '', key)
    
    return key

def get_clean_openai_key():
    """
    Получает и проверяет ключ OpenAI API из переменных окружения.
    Пытается автоматически исправить распространенные проблемы с форматом.
    
    Возвращает:
    - Валидный ключ API или None, если ключ не найден или неверен
    """
    api_key = os.environ.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("ОШИБКА: Ключ API OpenAI не найден в переменных окружения")
        return None
        
    fixed_key = fix_key_format(api_key)
    
    if fixed_key and validate_openai_key(fixed_key):
        if fixed_key != api_key:
            print("Формат ключа API был исправлен автоматически")
        return fixed_key
    else:
        print(f"ОШИБКА: Ключ API имеет неверный формат: {api_key[:5]}...")
        return None

def update_env_file_with_key(new_key):
    """
    Обновляет файл .env с новым ключом API
    """
    env_path = Path('.env')
    
    if not env_path.exists():
        # Если .env не существует, создаем его
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(f'OPENAI_API_KEY={new_key}\n')
        return True
        
    # Если файл существует, обновляем значение
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    key_found = False
    new_lines = []
    
    for line in lines:
        if line.startswith('OPENAI_API_KEY='):
            new_lines.append(f'OPENAI_API_KEY={new_key}\n')
            key_found = True
        else:
            new_lines.append(line)
            
    if not key_found:
        new_lines.append(f'OPENAI_API_KEY={new_key}\n')
        
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    return True

def check_api_connectivity(api_key):
    """
    Проверяет связь с API OpenAI с использованием предоставленного ключа
    
    Возвращает:
    - Кортеж (успех, сообщение)
    """
    try:
        import openai
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        
        return True, f"Соединение установлено успешно. Доступно {len(models.data)} моделей."
    except Exception as e:
        return False, f"Ошибка соединения: {str(e)}"

if __name__ == "__main__":
    print("OpenAI API Key Helper")
    print("====================")
    
    # Получаем текущий ключ API
    current_key = get_clean_openai_key()
    
    if current_key:
        print(f"Текущий ключ API: {current_key[:10]}...{current_key[-5:]}")
        success, message = check_api_connectivity(current_key)
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            
            # Предлагаем обновить ключ
            print("\nХотите ввести новый ключ API? (y/n)")
            choice = input().lower()
            
            if choice == 'y':
                print("Введите новый ключ API:")
                new_key = input().strip()
                
                fixed_key = fix_key_format(new_key)
                if validate_openai_key(fixed_key):
                    success, message = check_api_connectivity(fixed_key)
                    
                    if success:
                        print(f"✅ {message}")
                        update_env_file_with_key(fixed_key)
                        print("Ключ API обновлен успешно!")
                    else:
                        print(f"❌ {message}")
                else:
                    print("❌ Введенный ключ имеет неверный формат")
    else:
        print("Введите новый ключ API:")
        new_key = input().strip()
        
        fixed_key = fix_key_format(new_key)
        if validate_openai_key(fixed_key):
            success, message = check_api_connectivity(fixed_key)
            
            if success:
                print(f"✅ {message}")
                update_env_file_with_key(fixed_key)
                print("Ключ API настроен успешно!")
            else:
                print(f"❌ {message}")
        else:
            print("❌ Введенный ключ имеет неверный формат")