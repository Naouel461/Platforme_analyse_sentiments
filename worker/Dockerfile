FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements.txt
COPY worker/requirements.txt /app/requirements.txt

# Installer PyTorch depuis le miroir officiel (plus rapide)
RUN pip install --no-cache-dir --default-timeout=1000 \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.0

# Installer les autres dépendances
RUN pip install --no-cache-dir --default-timeout=1000 \
    redis==5.0.1 \
    psycopg2-binary==2.9.9 \
    minio==7.2.7 \
    requests==2.31.0 \
    transformers==4.36.0 \
    numpy==1.24.3

# Copier le code
COPY sentiment_analyzer.py /app/
COPY worker/worker.py /app/

CMD ["python", "worker.py"]