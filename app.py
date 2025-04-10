# Файл: app/app.py

from flask import Flask, request, jsonify, send_file, make_response, render_template, session, redirect, url_for
from flask_cors import CORS
import openai
import tempfile
import os
import io 
import json
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from urllib.parse import quote
from utils.auth import is_logged_in, require_login, ADMIN_USERNAME, ADMIN_PASSWORD
from utils.vector_store import search_knowledgebase
from utils.products import get_product_info, add_product, list_all_products
from utils.calendar import create_calendar_event, list_calendar_events, find_free_slots
from config import OPENAI_API_KEY, ASSISTANT_ID, FLASK_SECRET_KEY, DIALOGUES_FILE

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-dev-key") 

CORS(app)
openai.api_key = OPENAI_API_KEY

# Завантаження існуючих діалогів
if os.path.exists(DIALOGUES_FILE):
    with open(DIALOGUES_FILE, "r", encoding="utf-8-sig") as f:
        dialogues = json.load(f)
else:
    dialogues = {}

# 🌍 Отримати мову з cookie
def get_lang():
    lang = request.cookies.get("site_lang", "uk")
    return lang if lang in ["uk", "en", "de"] else "uk"

# 📄 Вибрати шаблон залежно від мови
def t(name, **kwargs):
    lang = get_lang()
    template = f"{name}.html" if lang == "uk" else f"{name}_{lang}.html"
    return render_template(template, **kwargs)

# 🌐 Головна сторінка
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
            filename = secure_filename(file.filename)
            save_path = os.path.join("storage", "knowledgebase", filename)
            file.save(save_path)
            message = {
                "uk": f"Файл '{filename}' успішно завантажено!",
                "en": f"File '{filename}' uploaded successfully!",
                "de": f"Datei '{filename}' erfolgreich hochgeladen!"
            }.get(get_lang(), "Done")
    return t("upload_knowledge", message=message)

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

@app.route("/set_widget_settings", methods=["POST"])
@require_login
def set_widget_settings():
    interaction_mode = request.form.get("interaction_mode", "voice+chat")
    settings_path = "static/widget_settings.json"
    settings = {"interaction_mode": interaction_mode}
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    return redirect(url_for("dashboard"))


@app.route("/process_audio", methods=["POST"])
def process_audio():
    if "file" not in request.files or "client_id" not in request.form:
        return jsonify({"error": "Missing file or client_id"}), 400

    audio_file = request.files["file"]
    client_id = request.form["client_id"]

    # 📦 Читаємо байти, створюємо потік
    audio_bytes = audio_file.read()
    audio_stream = io.BytesIO(audio_bytes)

    print("📥 Отримано аудіо, розмір:", len(audio_bytes), "байт")

    # 🧠 Whisper API
    transcription = openai.audio.transcriptions.create(
        model="whisper-1",
        file=("audio.webm", audio_stream, "audio/webm")
    )

    user_message = transcription.text.strip()
    print("🗣️ Користувач сказав:", user_message)

    # Інструкція
    instruction_path = "storage/instructions.txt"
    if os.path.exists(instruction_path):
        with open(instruction_path, "r", encoding="utf-8") as f:
            assistant_instructions = f.read().strip()
    else:
        assistant_instructions = "Ти — ввічливий асистент. Відповідай коротко й коректно."

    # Пошук у базі знань
    knowledge = search_knowledgebase(user_message)
    full_message = (
        f"📌 Інструкція:\n{assistant_instructions}\n\n"
        f"📚 Контекст із бази знань:\n{knowledge}\n\n"
        f"🗣️ Питання користувача:\n{user_message}"
    )
    print("🧠 Повідомлення до GPT:\n", full_message)

    # GPT Threads API
    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=full_message
    )
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    while True:
        status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if status.status == "completed":
            break
        elif status.status == "requires_action":
            tool_outputs = []
            for tool_call in status.required_action.submit_tool_outputs.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                print(f"🔧 Виклик функції: {func_name}")
                print(f"📥 Аргументи: {json.dumps(args, ensure_ascii=False, indent=2)}")

                try:
                    if func_name == "get_product_info":
                        result = get_product_info(**args)
                    elif func_name == "add_product":
                        result = add_product(**args)
                    elif func_name == "create_calendar_event":
                        result = create_calendar_event(**args)
                        result += "\n\n⚠️ Це тестова подія. Для підтвердження зв'яжіться з представником."
                    elif func_name == "list_calendar_events":
                        result = list_calendar_events()
                    elif func_name == "list_all_products":
                        result = list_all_products()
                    elif func_name == "find_free_slots":
                        result = find_free_slots(**args)
                    else:
                        result = f"❌ Невідома функція: {func_name}"

                    print(f"✅ Результат:\n{result}")
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": result
                    })
                except Exception as e:
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": f"❌ Помилка: {str(e)}"
                    })

            openai.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
        elif status.status == "failed":
            return jsonify({"error": "Assistant failed"}), 500

        time.sleep(1)

    # Відповідь GPT
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value.strip()
    print("✅ GPT відповів:", answer)

    # 🎤 TTS
    speech_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    tts = openai.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=answer
    )
    with open(speech_file_path, "wb") as out:
        out.write(tts.content)

    # 🔖 Логування
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": user_message,
        "answer": answer
    }
    if client_id in dialogues:
        dialogues[client_id].append(log_entry)
    else:
        dialogues[client_id] = [log_entry]

    with open(DIALOGUES_FILE, "w", encoding="utf-8") as f:
        json.dump(dialogues, f, indent=2, ensure_ascii=False)

    # 📨 Відповідь користувачу
    response = make_response(send_file(speech_file_path, mimetype="audio/mpeg"))
    response.headers["X-Assistant-Answer"] = quote(answer)
    response.headers["X-User-Text"] = quote(user_message)
    response.headers["Access-Control-Expose-Headers"] = "X-Assistant-Answer, X-User-Text"
    return response

# Новий роут для текстових запитів
@app.route("/process_text", methods=["POST"])
def process_text():
    data = request.get_json()
    text = data.get("text", "")
    client_id = data.get("client_id", "unknown")

    if not text:
        return jsonify({"error": "Порожній запит"}), 400

    # Інструкція
    instruction_path = "storage/instructions.txt"
    if os.path.exists(instruction_path):
        with open(instruction_path, "r", encoding="utf-8") as f:
            assistant_instructions = f.read().strip()
    else:
        assistant_instructions = "Ти — ввічливий асистент. Відповідай коротко й коректно."

    knowledge = search_knowledgebase(text)
    full_message = (
        f"📌 Інструкція:\n{assistant_instructions}\n\n"
        f"📚 Контекст із бази знань:\n{knowledge}\n\n"
        f"🗣️ Питання користувача:\n{text}"
    )

    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=full_message
    )
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    while True:
        status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if status.status == "completed":
            break
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value.strip()

    # Логування
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": text,
        "answer": answer
    }
    if client_id in dialogues:
        dialogues[client_id].append(log_entry)
    else:
        dialogues[client_id] = [log_entry]

    with open(DIALOGUES_FILE, "w", encoding="utf-8") as f:
        json.dump(dialogues, f, indent=2, ensure_ascii=False)

    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

