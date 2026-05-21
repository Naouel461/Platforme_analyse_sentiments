FROM python:3.11-slim

# Définir le dossier de travail dans le conteneur
WORKDIR /app

# Copier le fichier des dépendances
COPY worker/requirements.txt /app/requirements.txt

# Installer les bibliothèques nécessaires au worker
RUN pip install -r requirements.txt

# Copier les scripts Python du service
COPY worker/worker.py /app/worker.py
COPY sentiment_analyzer.py /app/sentiment_analyzer.py

# Exécuter le worker au démarrage du conteneur
CMD ["python", "worker.py"]