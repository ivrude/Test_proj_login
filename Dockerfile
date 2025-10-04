FROM python:3.12-slim

# Робоча директорія
WORKDIR /app

# Копіюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код
COPY . .

# Порт
EXPOSE 8000

# Команда запуску
CMD ["uvicorn", "app.api:app", "--reload"]
