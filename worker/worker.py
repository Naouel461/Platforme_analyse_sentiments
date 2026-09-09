import os
import json
import time
import sys
import redis
import psycopg2
import re
from datetime import datetime

print("=== WORKER DEMARRAGE ===", flush=True)

# ============================================
# 1. CONNEXIONS
# ============================================

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    print(f"✅ Redis OK ({REDIS_HOST}:{REDIS_PORT})", flush=True)
except Exception as e:
    print(f"❌ Redis erreur: {e}", flush=True)
    sys.exit(1)

# PostgreSQL
DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "Naouel")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Pino2026")
DB_NAME = os.getenv("DB_NAME", "sentiment_db")

conn = None
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=5432,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    print(f"✅ PostgreSQL OK ({DB_HOST})", flush=True)
    
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            sentiment VARCHAR(20),
            confidence FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    print("✅ Table predictions prête", flush=True)
except Exception as e:
    print(f"⚠️ DB: {e}", flush=True)
    conn = None

print("=== WORKER PRET ===", flush=True)

# ============================================
# 2. FONCTION D'ANALYSE SIMPLIFIÉE (sans PyTorch)
# ============================================

def analyser_sentiment_simple(texte):
    """Analyse de sentiment par mots-clés (fallback)"""
    texte = texte.lower()
    
    # Mots positifs
    positifs = [
        'excellent', 'genial', 'génial', 'super', 'formidable', 'parfait',
        'bon', 'bien', 'content', 'satisfait', 'ravi', 'heureux', 'top',
        'superbe', 'magnifique', 'extraordinaire', 'remarquable', 'parfait'
    ]
    
    # Mots négatifs
    negatifs = [
        'nul', 'mauvais', 'horrible', 'terrible', 'déçu', 'decu',
        'catastrophe', 'déplorable', 'triste', 'dommage', 'pire',
        'dégoutant', 'dégoûtant', 'affreux', 'abominable'
    ]
    
    score = 0
    for mot in positifs:
        if mot in texte:
            score += 1
    for mot in negatifs:
        if mot in texte:
            score -= 1
    
    # Émoticônes
    if any(e in texte for e in ['😊', '❤️', '👍', '😍', '🥰', '🎉']):
        score += 1
    if any(e in texte for e in ['😡', '👎', '💔', '😭', '🤬']):
        score -= 1
    
    if score > 0:
        return "POSITIVE", min(0.8, 0.6 + (score * 0.05))
    elif score < 0:
        return "NEGATIVE", min(0.8, 0.6 + (abs(score) * 0.05))
    else:
        return "NEUTRAL", 0.55

# ============================================
# 3. FONCTION D'EXTRACTION DE TEXTE
# ============================================

def extraire_texte(data):
    if not data:
        return None
    
    data = data.strip()
    
    # Nettoyage des backslashes
    while '\\\\' in data:
        data = data.replace('\\\\', '\\')
    data = data.replace('\\:', ':').replace('\\{', '{').replace('\\}', '}')
    
    # Essayer de parser le JSON
    try:
        task = json.loads(data)
        return task.get('text', '')
    except:
        pass
    
    # Recherche par regex
    match = re.search(r'text\s*[:=]\s*["\']([^"\']+)["\']', data)
    if match:
        return match.group(1)
    
    # Nettoyage final
    clean = re.sub(r'[^a-zA-Zàâçéèêëîïôûùüÿñæœ\s\-\.\,\!\?]', ' ', data)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    if len(clean) > 2:
        return clean
    
    return re.sub(r'[^\x20-\x7E]', '', data)

# ============================================
# 4. BOUCLE PRINCIPALE
# ============================================

print("🔄 En attente des tâches...", flush=True)

while True:
    try:
        result = r.blpop('sentiment_tasks', timeout=2)
        if result:
            _, data = result
            print(f"📨 Reçu: {data[:60]}...", flush=True)
            
            # Extraire le texte
            text = extraire_texte(data)
            
            if not text or len(text.strip()) < 2:
                print("⚠️ Texte trop court ou invalide, ignoré", flush=True)
                continue
            
            text = text.strip()
            print(f"📊 Analyse: {text[:40]}...", flush=True)
            
            # Analyser
            sentiment, confidence = analyser_sentiment_simple(text)
            
            # Sauvegarde Redis
            response = {
                'sentiment': sentiment.upper(),
                'confidence': confidence,
                'text': text,
                'timestamp': datetime.now().isoformat()
            }
            r.rpush('sentiment_results', json.dumps(response))
            print(f"💾 Redis: {sentiment}", flush=True)
            
            # Sauvegarde PostgreSQL
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO predictions (text, sentiment, confidence) VALUES (%s, %s, %s)",
                        (text, sentiment.upper(), confidence)
                    )
                    conn.commit()
                    cur.close()
                    print(f"💾 DB: {sentiment}", flush=True)
                except Exception as e:
                    print(f"⚠️ DB error: {e}", flush=True)
            
            print("✅ OK", flush=True)
            
    except KeyboardInterrupt:
        print("🛑 Arrêt demandé", flush=True)
        break
    except Exception as e:
        print(f"⚠️ Erreur: {e}", flush=True)
        time.sleep(1)