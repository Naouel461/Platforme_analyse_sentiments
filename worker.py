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
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            key_hash VARCHAR(255) NOT NULL,
            name VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sources (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            display_name VARCHAR(100),
            base_url VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS searches (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            keyword VARCHAR(255) NOT NULL,
            source_id INTEGER REFERENCES sources(id),
            limit_requested INTEGER DEFAULT 10,
            results_count INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            search_id INTEGER REFERENCES searches(id) ON DELETE CASCADE,
            source_id INTEGER REFERENCES sources(id),
            text TEXT NOT NULL,
            sentiment VARCHAR(20) CHECK (sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL')),
            confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
            language VARCHAR(10) DEFAULT 'multi',
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS feedbacks (
            id SERIAL PRIMARY KEY,
            prediction_id INTEGER REFERENCES predictions(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            is_correct BOOLEAN NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_predictions_sentiment ON predictions(sentiment);
        CREATE INDEX IF NOT EXISTS idx_predictions_search_id ON predictions(search_id);
        CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_searches_user_id ON searches(user_id);

        INSERT INTO sources (name, display_name, base_url)
        VALUES ('google', 'Google Maps', 'https://maps.google.com')
        ON CONFLICT (name) DO NOTHING;

        INSERT INTO users (username, email, password_hash, role)
        VALUES ('admin', 'admin@sentiment.tn', 'hash_a_changer', 'admin')
        ON CONFLICT (username) DO NOTHING;
    """)
    conn.commit()
    cur.close()
    print("✅ Toutes les tables créées", flush=True)
except Exception as e:
    print(f"⚠️ DB: {e}", flush=True)
    conn = None

print("=== WORKER PRET ===", flush=True)

# ============================================
# 2. FONCTION D'ANALYSE SIMPLIFIÉE
# ============================================

def analyser_sentiment_simple(texte):
    """Analyse de sentiment par mots-clés (fallback)"""
    texte = texte.lower()

    positifs = [
        'excellent', 'genial', 'génial', 'super', 'formidable', 'parfait',
        'bon', 'bien', 'content', 'satisfait', 'ravi', 'heureux', 'top',
        'superbe', 'magnifique', 'extraordinaire', 'remarquable'
    ]

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

    while '\\\\' in data:
        data = data.replace('\\\\', '\\')
    data = data.replace('\\:', ':').replace('\\{', '{').replace('\\}', '}')

    try:
        task = json.loads(data)
        return task.get('text', '')
    except:
        pass

    match = re.search(r'text\s*[:=]\s*["\']([^"\']+)["\']', data)
    if match:
        return match.group(1)

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

            text = extraire_texte(data)

            if not text or len(text.strip()) < 2:
                print("⚠️ Texte trop court ou invalide, ignoré", flush=True)
                continue

            text = text.strip()
            print(f"📊 Analyse: {text[:40]}...", flush=True)

            sentiment, confidence = analyser_sentiment_simple(text)

            response = {
                'sentiment': sentiment.upper(),
                'confidence': confidence,
                'text': text,
                'timestamp': datetime.now().isoformat()
            }
            r.rpush('sentiment_results', json.dumps(response))
            print(f"💾 Redis: {sentiment}", flush=True)

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