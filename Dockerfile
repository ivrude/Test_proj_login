FROM python:3.12-slim

# Робоча директорія
WORKDIR /app

# Копіюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код
COPY . .

# Порт
EXPOSE 8001

# Команда запуску
CMD ["uvicorn", "api:app","--host", "0.0.0.0", "--port", "8001", "--reload"]
