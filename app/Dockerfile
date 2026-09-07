# Utilisation de la version slim pour pas que l'image pèse 3 tonnes
FROM python:3.11-slim

# On se met dans /app, c'est plus propre
WORKDIR /app

# --- Setup du système ---
# Besoin de gcc pour compiler certaines libs python un peu capricieuses
RUN apt-get update && apt-get install -y \
    gcc \
    g++ && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Installation des packages ---
# On copie d'abord le fichier de dépendances
COPY requirements.txt /app/requirements.txt

# On installe tout, et on rajoute redis manuellement (oublié dans le txt ?)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt redis

# --- Code source ---
# On récupère tout le reste du projet ici
COPY . /app

# Port 8000 pour l'API
EXPOSE 8000

# Note: on garde le --reload uniquement pour le dev, à virer en prod !
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
