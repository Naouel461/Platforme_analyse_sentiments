# ============================================================
# FICHIER : worker.py
# RÔLE : Worker Redis avec BERT (vraiment asynchrone)
# ============================================================

import os
import json
import time
import sys
import redis
import psycopg2
import re
from datetime import datetime
from transformers import pipeline
import torch

print("=== WORKER BERT DEMARRAGE ===", flush=True)

# ============================================
# 1. CONNEXIONS
# ============================================
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    print(f"✅ Redis OK ({REDIS_HOST}:{REDIS_PORT})", flush=True)
except Exception as e:
    print(f"❌ Redis erreur: {e}", flush=True)
    sys.exit(1)

DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "Naouel")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Pino2026")
DB_NAME = os.getenv("DB_NAME", "sentiment_db")

conn = None
try:
    conn = psycopg2.connect(
        host=DB_HOST, port=5432,
        user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    print(f"✅ PostgreSQL OK ({DB_HOST})", flush=True)
except Exception as e:
    print(f"⚠️ DB: {e}", flush=True)

# ============================================
# 2. CHARGEMENT DE BERT
# ============================================
print("🚀 Chargement du modèle BERT...", flush=True)
device = 0 if torch.cuda.is_available() else -1
classifier = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    device=device,
    truncation=True,
    max_length=512
)
print("✅ Modèle BERT chargé", flush=True)

cache_pred = {}

def analyser_bert(texte):
    """Analyse avec BERT, retourne (sentiment, score)"""
    if not texte or len(texte.strip()) < 3:
        return "NEUTRAL", 0.0

    if texte in cache_pred:
        return cache_pred[texte]

    try:
        result = classifier(texte)[0]
        stars = int(result['label'].split()[0])
        score = (stars - 3) / 2
        if score > 0.2:
            sentiment = "POSITIVE"
        elif score < -0.2:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"
        cache_pred[texte] = (sentiment, abs(score))
        return cache_pred[texte]
    except Exception as e:
        print(f"⚠️ Erreur BERT: {e}", flush=True)
        return "NEUTRAL", 0.0

# ============================================
# 3. BOUCLE PRINCIPALE
# ============================================
print("🔄 En attente des tâches...", flush=True)

while True:
    try:
        result = r.blpop('sentiment_tasks', timeout=2)
        if result:
            _, data = result
            print(f"📨 Reçu: {data[:60]}...", flush=True)

            try:
                task = json.loads(data)
            except:
                print("⚠️ JSON invalide", flush=True)
                continue

            text = task.get('text', '').strip()
            search_id = task.get('search_id')
            source_id = task.get('source_id', 1)

            if not text or len(text) < 3:
                print("⚠️ Texte trop court", flush=True)
                continue

            print(f"📊 BERT analyse: {text[:40]}...", flush=True)
            sentiment, confidence = analyser_bert(text)
            print(f"✅ {sentiment} ({confidence})", flush=True)

            # Enregistrer en DB
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO predictions
                        (search_id, source_id, text, sentiment, confidence, language, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (search_id, source_id, text, sentiment, confidence, 'multi', None))
                    conn.commit()
                    cur.close()
                    print(f"💾 DB OK", flush=True)
                except Exception as e:
                    print(f"⚠️ DB error: {e}", flush=True)
                    conn.rollback()

            # Envoyer résultat dans Redis
            response = {
                'sentiment': sentiment,
                'confidence': confidence,
                'text': text,
                'search_id': search_id,
                'timestamp': datetime.now().isoformat()
            }
            r.rpush('sentiment_results', json.dumps(response))

    except KeyboardInterrupt:
        print("🛑 Arrêt", flush=True)
        break
    except Exception as e:
        print(f"⚠️ Erreur: {e}", flush=True)
        time.sleep(1)
