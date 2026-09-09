FROM python:3.11-slim

# Définir le dossier de travail
WORKDIR /app

# Copier les requirements
COPY requirements.txt /app/requirements.txt

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code
COPY . /app

# Exposer le port
EXPOSE 8000

# Lancer l'API UNIQUEMENT (pas le worker !)
CMD cd /app && uvicorn app.main:app --host 0.0.0.0 --port 8000