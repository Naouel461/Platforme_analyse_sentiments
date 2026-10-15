FROM python:3.11-slim

WORKDIR /app

# Dépendances système (pour Playwright, psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer Playwright + Chromium
RUN pip install playwright && playwright install --with-deps chromium

# Copier le code
COPY . .

# Port exposé
EXPOSE 8000

# Commande par défaut (sera surchargée par docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
