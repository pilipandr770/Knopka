# 🎙️ Rozum Voice Assistant

**Rozum Voice Assistant** is an embeddable smart voice widget powered by OpenAI. It allows website visitors to speak, get answers via GPT, listen to AI voice responses, and even see full chat history — all through a single line of code.

---

## 🚀 Features

- 🎤 Voice recording in-browser (up to 30 sec)
- 💬 GPT-based text and voice responses
- 📦 Search your product database (CSV)
- 📚 Private knowledgebase (PDF, DOCX, TXT, CSV)
- 📅 Calendar integration (event booking & availability)
- 🛠️ Admin dashboard to manage knowledge and settings
- 🌐 Multilingual support: Ukrainian 🇺🇦, English 🇬🇧, German 🇩🇪

---

## 🛠️ Installation

```bash
git clone https://github.com/yourname/rozum-voice-assistant.git
cd rozum-voice-assistant
pip install -r requirements.txt
python app.py
Then open your browser at:

http://127.0.0.1:5000
🌐 How to embed it
Just add this line in your website’s <body>:

html
Копіювати
Редагувати
<script src="https://yourdomain.com/static/voice-widget.js"></script>
🧰 Admin Features
Access admin dashboard via:

pgsql
Копіювати
Редагувати
/login  → default: admin / admin123
There you can:

Upload knowledgebase files

Edit GPT instructions

View user chat logs

Set interaction mode: voice-only or voice + chat

📁 Project Structure
graphql
Копіювати
Редагувати
voice_assistant_project/
├── app.py                     # Flask server
├── config.py                  # API keys and settings
├── static/
│   └── voice-widget.js        # frontend voice widget
├── templates/                 # Jinja2 HTML templates
├── storage/
│   ├── knowledgebase/         # files used for GPT context
│   ├── dialogues.json         # saved conversations
│   ├── calendar_events.json   # test calendar
│   └── products.csv           # product list (for Q&A)
├── utils/
│   ├── vector_store.py        # embeddings and search
│   ├── products.py            # product API
│   ├── calendar.py            # calendar functions
│   └── auth.py                # login handling
📦 Tech Stack
🧠 OpenAI (Whisper + GPT-4 + TTS)

🧩 FAISS / Embedding-based context search

🎤 JavaScript MediaRecorder API

🌍 Flask + Jinja2

🧪 Pandas, NumPy for data handling

📜 Legal & Privacy
This project is GDPR-compliant:

No cookies, tracking, or marketing

Local client_id per user (stored in browser)

Data processed only to fulfill assistant's functionality

See privacy.html and impressum.html for full details.

🌍 Language Support
User interface and assistant work in:

🇺🇦 Ukrainian

🇬🇧 English

🇩🇪 German

Language is auto-detected or can be switched manually.

📣 Try the Demo
Visit / and interact with the assistant via microphone. The system will respond by voice and optionally in chat, depending on mode.

🔒 License
MIT — free to use, adapt, and resell. Just keep attribution 💚

