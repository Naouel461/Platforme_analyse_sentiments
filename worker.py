import os
import json
import time
import redis
import psycopg2
from minio import Minio
from datetime import datetime

# IMPORTANT : Utiliser les identifiants CORRECTS
from sentiment_analyzer import mon_ia

# Connexions avec les bons identifiants
client_redis = redis.Redis(host='redis', port=6379, decode_responses=True)

def ouvrir_connexion_db():
    return psycopg2.connect(
        host='db',
        user='Naouel',        # Changé !
        password='Pino2026',  # Changé !
        database='sentiment_db'
    )

client_minio = Minio(
    'minio:9000',
    access_key='minioadmin',
    secret_key='minioadmin123',
    secure=False
)

def traiter_et_sauvegarder(donnees_tache):
    texte = donnees_tache.get('text', '')
    print(f"📝 Analyse : {texte[:50]}...")
    
    resultat = mon_ia(texte)
    print(f"🎯 Résultat : {resultat['sentiment']} (confiance: {resultat['confiance']})")
    
    try:
        conn = ouvrir_connexion_db()
        cur = conn.cursor()
        
        # Création table si elle n'existe pas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_results (
                id SERIAL PRIMARY KEY,
                text TEXT,
                sentiment VARCHAR(20),
                confidence FLOAT,
                language VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute(
            "INSERT INTO sentiment_results (text, sentiment, confidence, language) VALUES (%s, %s, %s, %s)",
            (texte, resultat['sentiment'], resultat['confiance'], resultat['lang'])
        )
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Sauvegardé en BDD")
    except Exception as e:
        print(f"❌ Erreur BDD : {e}")

print("🚀 Worker démarré, attente des tâches...")

while True:
    tache = client_redis.blpop('sentiment_tasks', timeout=5)
    if tache:
        print("📨 Tâche reçue !")
        infos = json.loads(tache[1])
        traiter_et_sauvegarder(infos)