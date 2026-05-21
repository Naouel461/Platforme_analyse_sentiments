# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys

# Permet d'importer les fichiers du dossier courant
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

app = FastAPI(
    title="Sentiment Analysis API",
    version="2.0.0"
)

# Autoriser les appels depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Structure de la requête reçue
class TexteRequest(BaseModel):
    text: str


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "Sentiment Analysis API - Modele Multilingue",
        "version": "2.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "sentiment-api"
    }


@app.post("/predict")
def predict(request: TexteRequest):
    from sentiment_analyzer import mon_ia

    resultat = mon_ia(request.text)

    return {
        "text": request.text,
        "sentiment": resultat["sentiment"],
        "confidence": resultat["confiance"],
        "language": resultat["lang"]
    }


@app.get("/stats")
def get_stats():
    import psycopg2

    try:
        connexion = psycopg2.connect(
            host="db",
            user="Naouel",
            password="Pino2026",
            database="sentiment_db"
        )

        curseur = connexion.cursor()

        curseur.execute("""
            SELECT sentiment, COUNT(*) as count
            FROM sentiment_results
            GROUP BY sentiment
        """)

        stats = dict(curseur.fetchall())

        curseur.close()
        connexion.close()

        return {"stats": stats}

    except Exception as erreur:
        return {"error": str(erreur)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )