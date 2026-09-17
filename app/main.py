import uvicorn
from fastapi import FastAPI, Query, Depends, HTTPException, Security, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from datetime import datetime
import warnings
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
import hashlib
import hmac
import base64
import secrets
from dotenv import load_dotenv
from transformers import pipeline
import torch
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from sqlalchemy.orm import Session
from database import get_db

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

load_dotenv()
warnings.filterwarnings('ignore')

REQUESTS = Counter('api_requests_total', 'Total des requêtes HTTP')
LATENCY = Histogram('api_latency_seconds', 'Latence des requêtes en secondes')

device = 0 if torch.cuda.is_available() else -1
classifier = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    device=device,
    truncation=True,
    max_length=512
)

cache_pred = {}

from collectors.google_reviews_scraper import collecter_avis_google_auto_sync

app = FastAPI(title="Analyse de sentiments - Google Reviews")
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        REQUESTS.inc()
        LATENCY.observe(duration)
        return response

app.add_middleware(PrometheusMiddleware)

# ============================================================
# AUTHENTIFICATION
# ============================================================
SECRET_KEY = os.getenv("SECRET_KEY", "changer_cette_cle_en_production")
TOKEN_TTL = 7 * 24 * 3600


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100_000)
    return f"{salt}${h.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split('$')
        computed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100_000)
        return hmac.compare_digest(expected, computed.hex())
    except Exception:
        return False


def create_token(user_id: int) -> str:
    payload = {"uid": user_id, "exp": int(time.time()) + TOKEN_TTL}
    b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET_KEY.encode(), b64.encode(), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"


def decode_token(token: str):
    try:
        b64, sig = token.split(".")
        expected = hmac.new(SECRET_KEY.encode(), b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        pad = "=" * (-len(b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(b64 + pad))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def get_current_user(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentification requise")
    payload = decode_token(authorization[7:])
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB error")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, username, email, role FROM users WHERE id = %s",
                    (payload["uid"],))
        user = cur.fetchone()
    finally:
        conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return dict(user)


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verifier_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=403, detail="❌ Clé API manquante")
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB error")
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1 FROM api_keys
            WHERE key_hash = %s AND is_active = TRUE
              AND (expires_at IS NULL OR expires_at > NOW())
        """, (key_hash,))
        if not cur.fetchone():
            raise HTTPException(status_code=403, detail="❌ Clé API invalide ou expirée")
        return api_key
    finally:
        conn.close()

# ============================================================
# Connexion DB
# ============================================================
def get_db_connection():
    try:
        host = os.getenv("DB_HOST", "localhost")
        if host == "":
            host = "localhost"
        conn = psycopg2.connect(
            host=host, port=5432,
            user='Naouel', password='Pino2026', database='sentiment_db'
        )
        return conn
    except Exception as e:
        print(f"[DB] ❌ Erreur: {e}")
        return None

# ============================================================
# Fonctions DB
# ============================================================
def save_search_and_predictions(keyword, source_name="google", limit=10, results=None, user_id=None):
    conn = get_db_connection()
    if not conn:
        return None, []
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM sources WHERE name = %s", (source_name,))
        source_row = cur.fetchone()
        source_id = source_row[0] if source_row else 1

        cur.execute("""
            INSERT INTO searches (keyword, source_id, limit_requested, results_count, status, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (keyword, source_id, limit, len(results) if results else 0, 'completed', user_id))
        search_id = cur.fetchone()[0]

        prediction_ids = []
        if results:
            for r in results:
                cur.execute("""
                    INSERT INTO predictions
                    (search_id, source_id, text, sentiment, sentiment_score, language, metadata_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    search_id, source_id,
                    r.get('text', ''), r.get('sentiment', 'NEUTRAL'),
                    r.get('sentiment_score', 0.0), r.get('language', 'multi'),
                    json.dumps(r.get('metadata')) if r.get('metadata') else None,
                ))
                prediction_ids.append(cur.fetchone()[0])

        conn.commit()
        return search_id, prediction_ids
    except Exception as e:
        print(f"[DB] ❌ Erreur insertion: {e}")
        conn.rollback()
        return None, []
    finally:
        conn.close()


def get_history(limit=50):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, text, sentiment, sentiment_score, metadata_json, created_at
            FROM predictions ORDER BY created_at DESC LIMIT %s
        """, (limit,))
        return cur.fetchall()
    except Exception as e:
        print(f"[DB] ❌ Erreur historique: {e}")
        return []
    finally:
        conn.close()


def get_stats():
    conn = get_db_connection()
    if not conn:
        return {}
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT COUNT(*) as total FROM predictions")
        total = cur.fetchone()['total']
        cur.execute("SELECT sentiment, COUNT(*) as count FROM predictions GROUP BY sentiment")
        repartition = cur.fetchall()
        cur.execute("""
            SELECT DATE(created_at) as jour, COUNT(*) as total,
                   SUM(CASE WHEN sentiment='POSITIVE' THEN 1 ELSE 0 END) as positifs,
                   SUM(CASE WHEN sentiment='NEGATIVE' THEN 1 ELSE 0 END) as negatifs,
                   SUM(CASE WHEN sentiment='NEUTRAL' THEN 1 ELSE 0 END) as neutres
            FROM predictions
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at) ORDER BY jour DESC
        """)
        daily = cur.fetchall()
        return {"total": total, "repartition": repartition, "daily": daily}
    except Exception as e:
        print(f"[DB] ❌ Erreur stats: {e}")
        return {}
    finally:
        conn.close()

# ============================================================
# Analyse de sentiment
# ============================================================
def analyser_sentiment(texte):
    if not texte or len(texte.strip()) < 3:
        return 0.0, "NEUTRAL"
    if texte in cache_pred:
        return cache_pred[texte]
    try:
        result = classifier(texte)[0]
        label = result['label']
        stars = int(label.split()[0])
        sentiment_score = (stars - 3) / 2
        if sentiment_score > 0.2:
            sentiment = "POSITIVE"
        elif sentiment_score < -0.2:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"
        cache_pred[texte] = (round(sentiment_score, 2), sentiment)
        return cache_pred[texte]
    except Exception as e:
        print(f"[Analyse] Erreur modèle: {e}")
        return 0.0, "NEUTRAL"

# ============================================================
# Pydantic models
# ============================================================
from pydantic import BaseModel

class TextInput(BaseModel):
    text: str

class RegisterModel(BaseModel):
    username: str
    email: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

class SiteFeedbackModel(BaseModel):
    rating: int | None = None
    message: str

# ============================================================
# AUTH ENDPOINTS
# ============================================================
@app.post("/auth/register")
def register(data: RegisterModel):
    if len(data.username.strip()) < 3:
        raise HTTPException(400, "Nom d'utilisateur trop court (min 3)")
    if "@" not in data.email or "." not in data.email:
        raise HTTPException(400, "Email invalide")
    if len(data.password) < 6:
        raise HTTPException(400, "Mot de passe trop court (min 6)")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(500, "DB error")
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s OR email = %s",
                    (data.username.strip(), data.email.strip()))
        if cur.fetchone():
            raise HTTPException(400, "Nom d'utilisateur ou email déjà utilisé")

        pwd_hash = hash_password(data.password)
        cur.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (%s, %s, %s, 'user') RETURNING id
        """, (data.username.strip(), data.email.strip(), pwd_hash))
        user_id = cur.fetchone()[0]
        conn.commit()
        return {
            "status": "success",
            "token": create_token(user_id),
            "user": {
                "id": user_id, "username": data.username.strip(),
                "email": data.email.strip(), "role": "user",
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        conn.close()


@app.post("/auth/login")
def login(data: LoginModel):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(500, "DB error")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, username, email, password_hash, role
            FROM users WHERE username = %s OR email = %s
        """, (data.username.strip(), data.username.strip()))
        user = cur.fetchone()
    finally:
        conn.close()

    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Identifiants incorrects")

    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user["id"],))
            conn.commit()
        finally:
            conn.close()

    return {
        "status": "success",
        "token": create_token(user["id"]),
        "user": {
            "id": user["id"], "username": user["username"],
            "email": user["email"], "role": user["role"],
        }
    }


@app.get("/auth/me")
def auth_me(user: dict = Depends(get_current_user)):
    return {"status": "success", "user": user}

# ============================================================
# Endpoints publics
# ============================================================
@app.get("/")
def home():
    return {"status": "online", "message": "Analyse d'avis Google Maps",
            "source": "Google Maps + DB Cache"}


@app.get("/recherche_avis")
def recherche_avis(mot_cle: str, limit: int = 5,
                   db: Session = Depends(get_db),
                   user: dict = Depends(get_current_user)):
    print(f"[Recherche] 🔍 {mot_cle} par {user['username']}")
    try:
        avis = collecter_avis_google_auto_sync(mot_cle, limit)
        results = []
        for avis_item in avis:
            texte = avis_item.get("texte", "")
            if texte and len(texte.strip()) >= 3:
                score, sentiment = analyser_sentiment(texte)
                results.append({
                    "text": texte, "sentiment": sentiment,
                    "sentiment_score": abs(score),
                    "note": avis_item.get("note", "N/A"),
                    "auteur": avis_item.get("auteur", "Anonyme"),
                    "metadata": {"note": avis_item.get("note"), "auteur": avis_item.get("auteur")}
                })

        search_id, prediction_ids = save_search_and_predictions(
            mot_cle, "google", limit, results, user_id=user["id"]
        )
        for i, r in enumerate(results):
            r["id"] = prediction_ids[i] if i < len(prediction_ids) else None

        return {"search_id": search_id, "keyword": mot_cle,
                "total": len(results), "data": results}
    except Exception as e:
        print(f"[Recherche] ⚠️ Erreur: {e}")
        return {"total": 0, "data": [], "error": str(e)}


@app.get("/recherches")
def get_recherches_endpoint(limit: int = Query(50)):
    conn = get_db_connection()
    if not conn:
        return {"total": 0, "data": []}
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT s.id, s.keyword, s.results_count, s.status,
                   s.created_at, s.user_id,
                   COALESCE(COUNT(p.id), 0) AS nb_predictions
            FROM searches s LEFT JOIN predictions p ON p.search_id = s.id
            GROUP BY s.id ORDER BY s.created_at DESC LIMIT %s
        """, (limit,))
        data = cur.fetchall()
        return {"total": len(data), "data": data}
    finally:
        conn.close()


@app.get("/recherches/{search_id}/predictions")
def get_predictions_by_search(search_id: int):
    conn = get_db_connection()
    if not conn:
        return {"total": 0, "data": []}
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, text, sentiment, sentiment_score, language, created_at
            FROM predictions WHERE search_id = %s ORDER BY id DESC
        """, (search_id,))
        data = cur.fetchall()
        return {"total": len(data), "data": data}
    finally:
        conn.close()


@app.get("/historique")
def get_historique_endpoint(limit: int = Query(50)):
    historique = get_history(limit)
    return {"total": len(historique), "data": historique}


@app.get("/stats")
def get_stats_endpoint():
    stats = get_stats()
    if not stats:
        return {"error": "Impossible de récupérer les statistiques"}
    return stats

# ============================================================
# Endpoint de test
# ============================================================
@app.post("/test-sentiment")
def test_sentiment(input: TextInput):
    score, sentiment = analyser_sentiment(input.text)
    return {"text": input.text, "sentiment": sentiment, "score": score}

# ============================================================
# Feedback du site (username + email copiés dans la table)
# ============================================================
@app.post("/site-feedback")
def post_site_feedback(feedback: SiteFeedbackModel,
                       user: dict = Depends(get_current_user)):
    if not feedback.message or len(feedback.message.strip()) < 3:
        raise HTTPException(status_code=400, detail="Le message est trop court")
    if feedback.rating is not None and not (1 <= feedback.rating <= 5):
        raise HTTPException(status_code=400, detail="La note doit être entre 1 et 5")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB error")
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO feedbacks (user_id, username, email, message, rating)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (
            user["id"],
            user.get("username"),
            user.get("email"),
            feedback.message.strip(),
            feedback.rating
        ))
        new_id = cur.fetchone()[0]
        conn.commit()
        return {"status": "success", "id": new_id, "message": "Merci pour votre retour !"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ============================================================
# Endpoints Admin
# ============================================================
@app.get("/admin/stats")
def admin_stats(api_key: str = Depends(verifier_api_key)):
    stats = get_stats()
    if not stats:
        return {"status": "error", "message": "Erreur stats"}
    return {"status": "success", "data": stats}


@app.get("/admin/feedbacks")
def admin_feedbacks(api_key: str = Depends(verifier_api_key),
                    limit: int = Query(200)):
    """Liste des feedbacks : id, user_id, username, email, rating, message."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB error")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, user_id, username, email, rating, message
            FROM feedbacks
            ORDER BY id DESC LIMIT %s
        """, (limit,))
        data = cur.fetchall()
        return {"total": len(data), "data": data}
    finally:
        conn.close()


@app.delete("/admin/feedbacks/{feedback_id}")
def delete_feedback(feedback_id: int,
                    api_key: str = Depends(verifier_api_key)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB error")
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM feedbacks WHERE id = %s", (feedback_id,))
        conn.commit()
        return {"status": "success", "deleted": cur.rowcount}
    finally:
        conn.close()


@app.post("/admin/reload-model")
def reload_model(api_key: str = Depends(verifier_api_key)):
    return {"status": "success", "message": "Modèle rechargé",
            "timestamp": datetime.now().isoformat()}

# ============================================================
# Prometheus Metrics
# ============================================================
@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)