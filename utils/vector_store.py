# utils/vector_store.py

import os
import json
import openai
from pathlib import Path
from uuid import uuid4

EMBED_MODEL = "text-embedding-3-small"
KB_DIR = Path("storage/knowledgebase")
VECTOR_DB_FILE = Path("storage/vector_store.json")

# Убедимся, что каталог для базы знаний существует
KB_DIR.mkdir(parents=True, exist_ok=True)

# Завантаження або створення словника
if VECTOR_DB_FILE.exists():
    with open(VECTOR_DB_FILE, "r", encoding="utf-8") as f:
        try:
            vector_db = json.load(f)
            if not isinstance(vector_db, list):
                vector_db = []
        except json.JSONDecodeError:
            vector_db = []
else:
    vector_db = []

def read_file(filepath: Path):
    if filepath.suffix == ".txt":
        return filepath.read_text(encoding="utf-8")
    elif filepath.suffix == ".csv":
        return filepath.read_text(encoding="utf-8")
    elif filepath.suffix == ".json":
        return filepath.read_text(encoding="utf-8")
    elif filepath.suffix == ".pdf":
        import fitz  # PyMuPDF
        text = ""
        with fitz.open(filepath) as doc:
            for page in doc:
                text += page.get_text()
        return text
    elif filepath.suffix == ".docx":
        from docx import Document
        doc = Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        return ""

def chunk_text(text, max_tokens=500):
    paragraphs = text.split("\n")
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) < max_tokens * 4:
            current += para + "\n"
        else:
            chunks.append(current.strip())
            current = para + "\n"
    if current:
        chunks.append(current.strip())
    return chunks

def embed_text(text):
    try:
        # Проверяем доступность глобального клиента
        if hasattr(openai, "client") and openai.client:
            try:
                # Используем глобальный клиент для API проекта
                res = openai.client.embeddings.create(
                    model=EMBED_MODEL,
                    input=text
                )
                return res.data[0].embedding
            except Exception as e:
                print(f"❌ Ошибка при использовании клиента для генерации эмбеддингов: {str(e)}")
                res = openai.embeddings.create(
                    model=EMBED_MODEL,
                    input=text
                )
                return res.data[0].embedding
        else:
            res = openai.embeddings.create(
                model=EMBED_MODEL,
                input=text
            )
            return res.data[0].embedding
    except Exception as e:
        print(f"❌ Критическая ошибка при генерации эмбеддингов: {str(e)}")
        return [0.0] * 1536

def index_knowledgebase():
    global vector_db
    new_entries = []

    # Index files from knowledgebase directory
    for file in KB_DIR.iterdir():
        text = read_file(file)
        if not text:
            continue
        chunks = chunk_text(text)
        for chunk in chunks:
            try:
                vector = embed_text(chunk)
                new_entries.append({
                    "id": str(uuid4()),
                    "text": chunk,
                    "embedding": vector,
                    "source": file.name
                })
            except Exception as e:
                print(f"❌ Error embedding chunk: {e}")

    # Index instructions
    instruction_file = Path("storage/instructions.txt")
    if instruction_file.exists():
        with open(instruction_file, "r", encoding="utf-8") as f:
            instructions = f.read().strip()
            if instructions:
                chunks = chunk_text(instructions)
                for chunk in chunks:
                    try:
                        vector = embed_text(chunk)
                        new_entries.append({
                            "id": str(uuid4()),
                            "text": chunk,
                            "embedding": vector,
                            "source": "instructions.txt"
                        })
                    except Exception as e:
                        print(f"❌ Error embedding instruction chunk: {e}")

    # Update vector_db with new entries
    vector_db.extend(new_entries)

    # Save to disk
    with open(VECTOR_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(vector_db, f, indent=2, ensure_ascii=False)
    print("✅ Векторна база знань оновлена.")

from numpy import dot
from numpy.linalg import norm
import numpy as np

def cosine_similarity(v1, v2):
    if not v1 or not v2:
        return 0
    return dot(v1, v2) / (norm(v1) * norm(v2))

def search_similar(query, top_k=3):
    try:
        query_embedding = embed_text(query)
        
        similarities = []
        for entry in vector_db:
            score = cosine_similarity(query_embedding, entry["embedding"])
            similarities.append((score, entry))
        
        # Sort by similarity score in descending order
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top k results
        results = []
        for score, entry in similarities[:top_k]:
            results.append({
                "text": entry["text"],
                "source": entry["source"],
                "score": float(score)
            })
        return results
    except Exception as e:
        print(f"❌ Error during similarity search: {str(e)}")
        return []

def get_context(query, min_similarity=0.7):
    results = search_similar(query)
    context = []
    
    for result in results:
        if result["score"] >= min_similarity:
            context.append(result["text"])
    
    return " ".join(context)

def search_knowledgebase(query, top_k=3):
    try:
        query_vec = embed_text(query)
        scored = []

        for item in vector_db:
            score = cosine_similarity(query_vec, item["embedding"])
            scored.append((score, item))

        scored.sort(reverse=True, key=lambda x: x[0])
        top_chunks = [item["text"] for score, item in scored[:top_k]]
        return "\n\n".join(top_chunks)
    except Exception as e:
        print(f"❌ Ошибка при поиске в базе знаний: {str(e)}")
        return "При поиске в базе знаний произошла ошибка. Пожалуйста, попробуйте задать вопрос иначе."
