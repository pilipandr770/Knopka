# 🐳 Dockerfile
FROM python:3.10-slim

# Встановлюємо робочий каталог
WORKDIR /app

# Копіюємо залежності та код
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Відкриваємо порт Flask
EXPOSE 5000

# Запускаємо застосунок
CMD ["python", "app.py"]
