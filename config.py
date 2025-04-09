import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
DIALOGUES_FILE = os.getenv("DIALOGUES_FILE", "storage/dialogues.json")
KNOWLEDGEBASE_DIR = os.getenv("KNOWLEDGEBASE_DIR", "storage/knowledgebase")
