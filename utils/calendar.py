# utils/calendar.py

import json
from pathlib import Path
from datetime import datetime, timedelta

CALENDAR_FILE = Path("storage/calendar_events.json")

def create_calendar_event(title: str, start_time: str, end_time: str, email: str = None) -> str:
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
    except Exception as e:
        return f"❌ Невірний формат дати: {e}"

    new_event = {
        "title": f"[ТЕСТ] {title}",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "email": email
    }

    events = []
    if CALENDAR_FILE.exists():
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            events = json.load(f)

    events.append(new_event)
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

    print(f"✅ Подія створена: {new_event}")
    return f"📅 Подія \"{title}\" створена як тестова на {start_time} – {end_time}."

def list_calendar_events() -> str:
    if not CALENDAR_FILE.exists():
        return "📭 Немає запланованих подій."

    with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
        events = json.load(f)

    now = datetime.utcnow()
    upcoming = [
        e for e in events if datetime.fromisoformat(e["start"]) > now
    ]

    if not upcoming:
        return "✅ Наразі всі слоти вільні."

    result = "📅 Найближчі події:\n"
    for e in upcoming[:5]:
        result += f"• {e['start']} – {e['end']} ({e['title']})\n"
    return result.strip()

def find_free_slots(duration_minutes=30, start_date=None, max_slots=3) -> str:
    now = datetime.utcnow()
    try:
        parsed = datetime.fromisoformat(start_date) if start_date else None
        start_time = parsed if parsed and parsed > now else now
    except:
        start_time = now

    end_of_day = start_time.replace(hour=23, minute=59)

    if not CALENDAR_FILE.exists():
        return "✅ Весь день вільний!"

    with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
        events = json.load(f)

    occupied = [
        (datetime.fromisoformat(e["start"]), datetime.fromisoformat(e["end"]))
        for e in events if datetime.fromisoformat(e["end"]) > now
    ]
    occupied.sort()

    free_slots = []
    current = start_time
    while current + timedelta(minutes=duration_minutes) <= end_of_day:
        conflict = False
        for start, end in occupied:
            if (start <= current < end) or (start < current + timedelta(minutes=duration_minutes) <= end):
                current = end
                conflict = True
                break
        if not conflict:
            slot_end = current + timedelta(minutes=duration_minutes)
            free_slots.append(f"{current.strftime('%Y-%m-%d %H:%M')} – {slot_end.strftime('%H:%M')}")
            current = slot_end
        if len(free_slots) >= max_slots:
            break

    print("🧪 Знайдено вільні слоти:")
    for s in free_slots:
        print("-", s)

    if not free_slots:
        return "❌ Сьогодні немає вільних слотів."

    return "🕓 Вільні слоти:\n" + "\n".join(free_slots)
