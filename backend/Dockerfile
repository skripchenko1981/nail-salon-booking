FROM python:3.11-slim

WORKDIR /app

# Встановлення системних залежностей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копіювання requirements та встановлення залежностей
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіювання коду застосунку
COPY backend/ .

# Відкриття порту
EXPOSE 8000

# Запуск застосунку
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]