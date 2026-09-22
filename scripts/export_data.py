# ============================================================
# FICHIER : scripts/export_data.py
# RÔLE : Exporte toutes les données PostgreSQL vers data/raw/
# USAGE : python scripts/export_data.py
# ============================================================

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'Naouel',
    'password': 'Pino2026',
    'dbname': 'sentiment_db'
}

os.makedirs("data/raw", exist_ok=True)


def export_predictions():
    print("📤 Export des predictions...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, text, sentiment, sentiment_score AS score,
               language, 'google' AS source, created_at AS date
        FROM predictions WHERE text IS NOT NULL ORDER BY id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    for row in rows:
        if row.get('date'):
            row['date'] = row['date'].isoformat()
    with open("data/raw/predictions.json", 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(rows)} prédictions exportées")
    return len(rows)


def export_feedbacks():
    print("📤 Export des feedbacks...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, message AS text, COALESCE(username, 'Anonyme') AS source,
               'site' AS origin, rating, COALESCE(email, '') AS email
        FROM feedbacks WHERE message IS NOT NULL ORDER BY id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    with open("data/raw/feedbacks.json", 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(rows)} feedbacks exportés")
    return len(rows)


def export_searches():
    print("📤 Export des recherches...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT s.id, s.keyword, s.results_count, s.status,
               s.created_at AS date, COUNT(p.id) AS nb_predictions
        FROM searches s LEFT JOIN predictions p ON p.search_id = s.id
        GROUP BY s.id ORDER BY s.id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    for row in rows:
        if row.get('date'):
            row['date'] = row['date'].isoformat()
    with open("data/raw/searches.json", 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(rows)} recherches exportées")
    return len(rows)


if __name__ == "__main__":
    print("=" * 60)
    print("  EXPORT DES DONNÉES PostgreSQL → data/raw/")
    print("=" * 60 + "\n")
    total = 0
    total += export_predictions()
    total += export_feedbacks()
    total += export_searches()
    print("\n" + "=" * 60)
    print(f"  ✅ TOTAL : {total} enregistrements exportés")
    print("=" * 60)
    print("\n📁 Fichiers dans data/raw/ :")
    for f in os.listdir("data/raw"):
        size = os.path.getsize(f"data/raw/{f}")
        print(f"  - {f} ({size} bytes)")