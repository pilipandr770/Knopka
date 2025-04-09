# Файл: app/app.py

from flask import Flask, request, jsonify, send_file, make_response, render_template, session, redirect, url_for
from flask_cors import CORS
import openai
import tempfile
import os
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
CORS(app)
openai.api_key = OPENAI_API_KEY
app.secret_key = FLASK_SECRET_KEY

# Завантаження існуючих діалогів
if os.path.exists(DIALOGUES_FILE):
    with open(DIALOGUES_FILE, "r", encoding="utf-8-sig") as f:
        dialogues = json.load(f)
else:
    dialogues = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/impressum")
def impressum():
    return render_template("impressum.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/process_audio", methods=["POST"])
def process_audio():
    if "file" not in request.files or "client_id" not in request.form:
        return jsonify({"error": "Missing file or client_id"}), 400

    audio_file = request.files["file"]
    client_id = request.form["client_id"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        audio_file.save(tmp.name)
        with open(tmp.name, "rb") as f:
            transcription = openai.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
    os.remove(tmp.name)
    user_message = transcription.text

    instruction_path = "storage/instructions.txt"
    if os.path.exists(instruction_path):
        with open(instruction_path, "r", encoding="utf-8") as f:
            assistant_instructions = f.read().strip()
    else:
        assistant_instructions = "Ти — ввічливий асистент. Відповідай коротко й коректно."

    knowledge = search_knowledgebase(user_message)
    full_message = (
        f"📌 Інструкція:\n{assistant_instructions}\n\n"
        f"📚 Контекст із бази знань:\n{knowledge}\n\n"
        f"🗣️ Питання користувача:\n{user_message}"
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

    # 🧠 Обробка функцій
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

                    print(f"✅ Результат функції:\n{result}\n{'-'*40}")
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": result
                    })
                except Exception as e:
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": f"❌ Помилка при виконанні: {str(e)}"
                    })

            openai.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
        elif status.status == "failed":
            return jsonify({"error": "Assistant failed"}), 500

        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value

    speech_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    tts_response = openai.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=answer
    )
    with open(speech_file_path, "wb") as out:
        out.write(tts_response.content)

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

    response = make_response(send_file(speech_file_path, mimetype="audio/mpeg"))
    response.headers["X-Assistant-Answer"] = quote(answer)
    response.headers["X-User-Text"] = quote(user_message)

    return response

# 🔐 Авторизація, інструкції, кабінет — залишились без змін нижче...

# (не дублюю решту — у тебе все там правильно 👌)


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
            error = "Невірний логін або пароль"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

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
            message = f"Файл '{filename}' успішно завантажено!"
    return render_template("upload_knowledge.html", message=message)

@app.route("/dashboard")
@require_login
def dashboard():
    return render_template("dashboard.html", dialogues=dialogues)

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
        message = "Інструкції оновлено успішно!"

    elif os.path.exists(instruction_file):
        with open(instruction_file, "r", encoding="utf-8") as f:
            content = f.read()

    return render_template("instructions.html", content=content, message=message)

if __name__ == "__main__":
    app.run(debug=True)
