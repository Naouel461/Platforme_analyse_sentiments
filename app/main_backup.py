# app/main.py - Version corrigée et minimaliste
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import json
import os
from datetime import datetime

# Création de l'application
app = FastAPI(title="Sentiment Analysis API", version="1.0.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèle pour les requêtes
class TexteRequest(BaseModel):
    text: str

class CollecteRequest(BaseModel):
    mot_cle: str
    limite: int = 10

# Connexion Redis
def get_redis():
    return redis.Redis(host='redis', port=6379, decode_responses=True)

# ========== ENDPOINTS ==========

@app.get("/")
def home():
    return {"status": "ok", "message": "API Sentiment Analysis", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "sentiment-api"}

@app.post("/predict")
def predict(request: TexteRequest):
    """Analyse un texte et retourne le sentiment"""
    from sentiment_analyzer import mon_ia
    
    resultat = mon_ia(request.text)
    return {
        "text": request.text,
        "sentiment": resultat["sentiment"],
        "confidence": resultat["confiance"],
        "language": resultat["lang"]
    }

@app.post("/collect-from-web")
def collect_from_web(request: CollecteRequest):
    """Collecte des avis depuis le web et les envoie à Redis"""
    r = get_redis()
    
    # Créer une tâche pour le worker
    tache = {
        "text": f"Recherche: {request.mot_cle} - Article exemple",
        "source": "web_collector",
        "mot_cle": request.mot_cle,
        "date": datetime.now().isoformat()
    }
    
    # Envoyer à Redis
    r.lpush('sentiment_tasks', json.dumps(tache))
    
    return {
        "status": "success",
        "message": f"Collecte lancée pour {request.mot_cle}",
        "taches_envoyees": 1
    }

@app.get("/stats")
def get_stats():
    """Récupère les statistiques des analyses"""
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            host='db',
            user='Naouel',
            password='Pino2026',
            database='sentiment_db'
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT sentiment, COUNT(*) as count 
            FROM sentiment_results 
            GROUP BY sentiment
        """)
        stats = dict(cur.fetchall())
        cur.close()
        conn.close()
        return {"stats": stats}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)