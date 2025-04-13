# 📁 app.py — повна версія з Whisper, GPT, OpenAI TTS і всіма маршрутами

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import openai
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from utils.auth import is_logged_in, require_login, ADMIN_USERNAME, ADMIN_PASSWORD
from utils.vector_store import search_knowledgebase
from utils.products import get_product_info, add_product, list_all_products
from utils.calendar import create_calendar_event, list_calendar_events, find_free_slots
from config import OPENAI_API_KEY, OPENAI_ORG_ID, ASSISTANT_ID, FLASK_SECRET_KEY, DIALOGUES_FILE
from urllib.parse import quote

# Отладочная информация о загруженных ключах
print(f"API Key loaded: {'Yes' if OPENAI_API_KEY else 'No'}")
if OPENAI_API_KEY:
    print(f"API Key type: {'Project Key' if OPENAI_API_KEY.startswith('sk-proj-') else 'Regular Key'}")
print(f"Assistant ID loaded: {'Yes' if ASSISTANT_ID else 'No'}")

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
CORS(app)

# Настройка клиента OpenAI с учетом типа ключа
if OPENAI_API_KEY:
    try:
        # Для ключей проекта (начинающихся с sk-proj-) используется новый метод инициализации
        if OPENAI_API_KEY.startswith('sk-proj-'):
            print("Initializing OpenAI client with project API key...")
            client_args = {"api_key": OPENAI_API_KEY}
            if OPENAI_ORG_ID:
                client_args["organization"] = OPENAI_ORG_ID
                
            # Создаем клиента с правильными параметрами
            openai_client = openai.OpenAI(**client_args)
            
            # Используем глобальную переменную для последующих вызовов
            openai.api_key = OPENAI_API_KEY
            if OPENAI_ORG_ID:
                openai.organization = OPENAI_ORG_ID
                
        else:
            # Стандартный метод инициализации для обычных ключей
            print("Initializing OpenAI client with standard API key...")
            openai.api_key = OPENAI_API_KEY
            if OPENAI_ORG_ID:
                openai.organization = OPENAI_ORG_ID
                
        # Проверка работоспособности API
        try:
            test_models = openai.models.list()
            print("✓ OpenAI API connection successful")
        except Exception as e:
            print(f"✗ OpenAI API connection failed: {str(e)}")
            
    except Exception as e:
        print(f"Error initializing OpenAI client: {str(e)}")

# Остальной код без изменений
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
        instruction_path = "storage/instructions.txt"
        assistant_instructions = "Ти — ввічливий асистент. Відповідай коротко й коректно."
        if os.path.exists(instruction_path):
            with open(instruction_path, "r", encoding="utf-8") as f:
                assistant_instructions = f.read().strip()

        knowledge = search_knowledgebase(text)
        full_message = f"📌 Інструкція:\n{assistant_instructions}\n\n📚 Контекст із бази знань:\n{knowledge}\n\n🗣️ Питання користувача:\n{text}"

        thread = openai.beta.threads.create()
        openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=full_message)
        run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)
        
        # Wait for completion with timeout
        start_time = time.time()
        max_wait_time = 30  # Maximum wait time in seconds
        
        while time.time() - start_time < max_wait_time:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            time.sleep(1)
            
        if run_status.status != "completed":
            return jsonify({"answer": "Вибачте, асистент не встиг обробити ваш запит. Спробуйте ще раз."})

        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        answer = messages.data[0].content[0].text.value.strip()

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
    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)
    run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)
    while openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id).status != "completed":
        time.sleep(1)
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value.strip()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
