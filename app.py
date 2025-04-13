# 📁 app.py — повна версія з Whisper, GPT, OpenAI TTS і всіма маршрутами

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import openai
from openai import OpenAI  # Импортируем конструктор клиента напрямую
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from utils.auth import is_logged_in, require_login, ADMIN_USERNAME, ADMIN_PASSWORD
from utils.vector_store import search_knowledgebase
from utils.products import get_product_info, add_product, list_all_products
from utils.calendar import create_calendar_event, list_calendar_events, find_free_slots
from config import OPENAI_API_KEY, OPENAI_ORG_ID, ASSISTANT_ID, FLASK_SECRET_KEY, DIALOGUES_FILE, openai_client_settings
from urllib.parse import quote

# Создаем глобальный клиент OpenAI
client = None
try:
    # Инициализация клиента OpenAI с настройками из config
    client = OpenAI(**openai_client_settings)
    print("✓ OpenAI клиент успешно инициализирован")
    
    # Проверяем соединение
    models = client.models.list()
    print(f"✓ Успешное соединение с API. Доступны {len(models.data)} моделей")
    
    # Также настраиваем модуль openai для обратной совместимости
    openai.api_key = OPENAI_API_KEY
    if OPENAI_ORG_ID:
        openai.organization = OPENAI_ORG_ID
    
    # Сохраняем клиент как глобальную переменную для использования в других модулях
    openai.client = client
except Exception as e:
    print(f"✗ Ошибка при инициализации OpenAI клиента: {e}")

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY  # Use the value from config
CORS(app)

# Остальной код без изменений...
if os.path.exists(DIALOGUES_FILE):
    with open(DIALOGUES_FILE, "r", encoding="utf-8-sig") as f:
        dialogues = json.load(f)
else:
    dialogues = {}

def get_lang():
    lang = request.cookies.get("site_lang", "uk")
    return lang if lang in ["uk", "en", "de"] else "uk"

def t(name, **kwargs):
    lang = get_lang()
    template = f"{name}.html" if lang == "uk" else f"{name}_{lang}.html"
    return render_template(template, **kwargs)

@app.route("/")
def index():
    return t("index")

@app.route("/privacy")
def privacy():
    return t("privacy")

@app.route("/impressum")
def impressum():
    return t("impressum")

@app.route("/contact")
def contact():
    return t("contact")

@app.route("/dashboard")
@require_login
def dashboard():
    return t("dashboard", dialogues=dialogues)

@app.route("/instructions", methods=["GET", "POST"])
@require_login
def instructions():
    instruction_file = "storage/instructions.txt"
    content = ""
    message = None
    if request.method == "POST":
        content = request.form.get("instructions", "")
        with open(instruction_file, "w", encoding="utf-8") as f:
            f.write(content)
        message = {
            "uk": "Інструкції оновлено успішно!",
            "en": "Instructions updated successfully!",
            "de": "Anweisungen erfolgreich gespeichert!"
        }.get(get_lang(), "Done")
    elif os.path.exists(instruction_file):
        with open(instruction_file, "r", encoding="utf-8") as f:
            content = f.read()
    return t("instructions", content=content, message=message)

@app.route("/upload_knowledge", methods=["GET", "POST"])
@require_login
def upload_knowledge():
    message = None
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            filename = file.filename
            file.save(os.path.join("storage", "knowledgebase", filename))
            message = {
                "uk": f"Файл '{filename}' успішно завантажено!",
                "en": f"File '{filename}' uploaded successfully!",
                "de": f"Datei '{filename}' erfolgreich hochgeladen!"
            }.get(get_lang(), "Done")
    return t("upload_knowledge", message=message)

@app.route("/set_widget_settings", methods=["POST"])
@require_login
def set_widget_settings():
    settings = {
        "interaction_mode": request.form.get("interaction_mode", "voice+chat"),
        "button": {
            "text": request.form.get("btn_text", "🎤"),
            "color": request.form.get("btn_color", "#ffffff"),
            "background": request.form.get("btn_bg", "#4CAF50"),
            "size": request.form.get("btn_size", "60px"),
            "position": request.form.get("btn_position", "bottom-right")
        }
    }
    with open("static/widget_settings.json", "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = {
                "uk": "Невірний логін або пароль",
                "en": "Invalid username or password",
                "de": "Falscher Benutzername oder Passwort"
            }.get(get_lang(), "Login failed")
    return t("login", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/process_audio", methods=["POST"])
def process_audio():
    try:
        audio_file = request.files.get("audio")
        client_id = request.form.get("client_id", "unknown")
        if not audio_file:
            return jsonify({"error": "Аудіофайл не знайдено"}), 400

        temp_filename = "temp_audio.webm"
        audio_file.save(temp_filename)
        with open(temp_filename, "rb") as f:
            transcription = openai.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="json"
            )
        os.remove(temp_filename)

        # Get the transcribed text
        text = transcription.text
        
        # Check if the text contains product or calendar related keywords
        text_lower = text.lower()
        
        # Handle product-related queries directly
        if any(keyword in text_lower for keyword in ["товар", "продукт", "склад", "інвентар", "наявність"]):
            try:
                if "список" in text_lower or "всі" in text_lower:
                    reply = list_all_products()
                else:
                    # Try to extract product name
                    import re
                    product_match = re.search(r'(?:товар|продукт|наявність)\s+[""]?([^""]+)[""]?', text_lower)
                    if product_match:
                        product_name = product_match.group(1).strip()
                        reply = get_product_info(product_name)
                    else:
                        # If no specific product mentioned, list all products
                        reply = list_all_products()
            except Exception as e:
                print(f"Error handling product query: {e}")
                reply = f"Виникла помилка при роботі з базою товарів: {str(e)}"
        
        # Handle calendar-related queries directly
        elif any(keyword in text_lower for keyword in ["календар", "запис", "прийом", "вільні", "слоти", "встреча", "встречу", "встретиться", "записаться"]):
            # Перенаправление на форму записи вместо попытки работы с календарем напрямую
            site_url = request.host_url.rstrip('/')
            booking_url = f"{site_url}/booking"
            
            # Подготовка ответа с ссылкой на форму бронирования
            if "ru" in text_lower or "рус" in text_lower:
                reply = f"Для записи на встречу, пожалуйста, заполните форму по ссылке: {booking_url}\n\nВы сможете выбрать удобную дату и время, а также указать тему встречи."
            else:
                reply = f"Для запису на зустріч, будь ласка, заповніть форму за посиланням: {booking_url}\n\nВи зможете вибрати зручну дату та час, а також вказати тему зустрічі."
        
        # For all other queries, use the OpenAI assistant
        else:
            reply = ask_gpt(text)

        # Save dialogue history
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "question": text,
            "answer": reply
        }
        dialogues.setdefault(client_id, []).append(log_entry)
        with open(DIALOGUES_FILE, "w", encoding="utf-8") as f:
            json.dump(dialogues, f, indent=2, ensure_ascii=False)

        speech = openai.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=reply
        )

        response = app.response_class(
            response=speech.read(),
            mimetype="audio/mpeg"
        )
        response.headers["X-Assistant-Answer"] = quote(reply)
        response.headers["X-User-Text"] = quote(text)
        return response

    except Exception as e:
        print(f"[process_audio] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/process_text", methods=["POST"])
def process_text():
    data = request.get_json()
    text = data.get("text", "")
    client_id = data.get("client_id", "unknown")
    if not text:
        return jsonify({"error": "Порожній запит"}), 400

    # Check if the text contains product or calendar related keywords
    text_lower = text.lower()
    
    # Handle product-related queries directly
    if any(keyword in text_lower for keyword in ["товар", "продукт", "склад", "інвентар", "наявність"]):
        try:
            if "список" in text_lower or "всі" in text_lower:
                answer = list_all_products()
            else:
                # Try to extract product name
                import re
                product_match = re.search(r'(?:товар|продукт|наявність)\s+[""]?([^""]+)[""]?', text_lower)
                if product_match:
                    product_name = product_match.group(1).strip()
                    answer = get_product_info(product_name)
                else:
                    # If no specific product mentioned, list all products
                    answer = list_all_products()
        except Exception as e:
            print(f"Error handling product query: {e}")
            answer = f"Виникла помилка при роботі з базою товарів: {str(e)}"
    
    # Handle calendar-related queries directly
    elif any(keyword in text_lower for keyword in ["календар", "запис", "прийом", "вільні", "слоти", "встреча", "встречу", "встретиться", "записаться"]):
        # Перенаправление на форму записи вместо попытки работы с календарем напрямую
        site_url = request.host_url.rstrip('/')
        booking_url = f"{site_url}/booking"
        
        # Подготовка ответа с ссылкой на форму бронирования
        if "ru" in text_lower or "рус" in text_lower:
            answer = f"Для записи на встречу, пожалуйста, заполните форму по ссылке: {booking_url}\n\nВы сможете выбрать удобную дату и время, а также указать тему встречи."
        else:
            answer = f"Для запису на зустріч, будь ласка, заповніть форму за посиланням: {booking_url}\n\nВи зможете вибрати зручну дату та час, а також вказати тему зустрічі."
    
    # For all other queries, use the OpenAI assistant
    else:
        try:
            instruction_path = "storage/instructions.txt"
            assistant_instructions = "Ти — ввічливий асистент. Відповідай коротко й коректно."
            if os.path.exists(instruction_path):
                with open(instruction_path, "r", encoding="utf-8") as f:
                    assistant_instructions = f.read().strip()

            knowledge = search_knowledgebase(text)
            full_message = f"📌 Інструкція:\n{assistant_instructions}\n\n📚 Контекст із бази знань:\n{knowledge}\n\n🗣️ Питання користувача:\n{text}"

            # Используем обновленную функцию ask_gpt
            answer = ask_gpt(full_message)
        except Exception as e:
            print(f"Error in process_text: {e}")
            answer = "Извините, произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."

    # Log the conversation
    log_entry = {"timestamp": datetime.utcnow().isoformat(), "question": text, "answer": answer}
    dialogues.setdefault(client_id, []).append(log_entry)
    with open(DIALOGUES_FILE, "w", encoding="utf-8") as f:
        json.dump(dialogues, f, indent=2, ensure_ascii=False)

    return jsonify({"answer": answer})

@app.route("/clear_history", methods=["POST"])
@require_login
def clear_history():
    global dialogues
    dialogues = {}
    with open(DIALOGUES_FILE, "w", encoding="utf-8") as f:
        json.dump(dialogues, f, indent=2, ensure_ascii=False)
    return redirect(url_for("dashboard"))

@app.route("/tts", methods=["GET"])
def text_to_speech():
    try:
        text = request.args.get("text", "")
        if not text:
            return jsonify({"error": "Текст не вказано"}), 400

        speech = openai.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )

        response = app.response_class(
            response=speech.read(),
            mimetype="audio/mpeg"
        )
        return response

    except Exception as e:
        print(f"[tts] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/booking", methods=["GET", "POST"])
def booking():
    message = None
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone", "")
        date = request.form.get("date")
        time = request.form.get("time")
        topic = request.form.get("topic")
        
        # Создаем новую запись в календаре
        booking_data = {
            "title": f"Встреча: {name}",
            "date": date,
            "time": time,
            "email": email,
            "phone": phone, 
            "topic": topic,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Сохраняем в файл booking.json
        booking_file = os.path.join("storage", "bookings.json")
        bookings = []
        if os.path.exists(booking_file):
            try:
                with open(booking_file, "r", encoding="utf-8") as f:
                    bookings = json.load(f)
            except json.JSONDecodeError:
                bookings = []
        
        bookings.append(booking_data)
        with open(booking_file, "w", encoding="utf-8") as f:
            json.dump(bookings, f, indent=2, ensure_ascii=False)
        
        message = "Спасибо! Ваша заявка принята. Мы свяжемся с вами для подтверждения встречи."
    
    return render_template("booking.html", message=message)

@app.route("/bookings")
@require_login
def view_bookings():
    # Загружаем данные о бронированиях
    booking_file = os.path.join("storage", "bookings.json")
    bookings = []
    if os.path.exists(booking_file):
        try:
            with open(booking_file, "r", encoding="utf-8") as f:
                bookings = json.load(f)
        except json.JSONDecodeError:
            bookings = []
    
    return render_template("bookings.html", bookings=bookings)

@app.route("/delete_booking", methods=["POST"])
@require_login
def delete_booking():
    index = int(request.form.get("index", -1))
    if index >= 0:
        booking_file = os.path.join("storage", "bookings.json")
        if os.path.exists(booking_file):
            try:
                with open(booking_file, "r", encoding="utf-8") as f:
                    bookings = json.load(f)
                
                if 0 <= index < len(bookings):
                    del bookings[index]
                    
                    with open(booking_file, "w", encoding="utf-8") as f:
                        json.dump(bookings, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error deleting booking: {e}")
    
    return redirect(url_for("view_bookings"))

def ask_gpt(prompt):
    try:
        # Проверяем, какой метод использовать для инициализации клиента
        if hasattr(openai, "client") and openai.client:
            # Используем клиентский метод для ключей проекта
            thread = openai.client.beta.threads.create()
            openai.client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)
            run = openai.client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)
            
            # Ждем завершения запроса
            while True:
                run_status = openai.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run_status.status == "completed":
                    break
                time.sleep(1)
            
            messages = openai.client.beta.threads.messages.list(thread_id=thread.id)
            return messages.data[0].content[0].text.value.strip()
        else:
            # Используем стандартный метод для обычных ключей
            thread = openai.beta.threads.create()
            openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)
            run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)
            
            # Ждем завершения запроса
            while True:
                run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run_status.status == "completed":
                    break
                time.sleep(1)
            
            messages = openai.beta.threads.messages.list(thread_id=thread.id)
            return messages.data[0].content[0].text.value.strip()
    except Exception as e:
        print(f"❌ Ошибка в запросе к OpenAI: {str(e)}")
        return f"Извините, произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже или свяжитесь с администратором."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
