import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from utils.vector_store import embed_text, vector_db
import json
from pathlib import Path
from uuid import uuid4

VECTOR_DB_FILE = Path("storage/knowledgebase/vector_store.json")

def extract_text_from_website(base_url, max_pages=10):
    visited = set()
    to_visit = [base_url]
    texts = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            visited.add(url)

            # Витягуємо текст
            main_text = soup.get_text(separator="\n", strip=True)
            if main_text:
                texts.append(main_text)

            # Знаходимо інші посилання на цьому ж домені
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                if base_url in link and link not in visited:
                    to_visit.append(link)
        except Exception as e:
            print(f"❌ {url}: {e}")
    return texts

def index_text_blocks(texts, source="website"):
    count = 0
    for text in texts:
        blocks = [t.strip() for t in text.split("\n") if len(t.strip()) > 50]
        for block in blocks:
            try:
                embedding = embed_text(block)
                vector_db.append({
                    "id": str(uuid4()),
                    "text": block,
                    "embedding": embedding,
                    "source": source
                })
                count += 1
            except Exception as e:
                print(f"❌ Skip block: {e}")
    with open(VECTOR_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(vector_db, f, indent=2, ensure_ascii=False)
    return count