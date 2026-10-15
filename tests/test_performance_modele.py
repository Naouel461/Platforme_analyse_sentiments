import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
import time
from app.sentiment_analyzer import mon_ia


def test_performance_modele():
    # 1. Charger le fichier Excel
    df = pd.read_excel("tests/data/test_avis.xlsx")

    # 2. Nettoyer les noms de colonnes (enlever virgules, espaces, tabulations)
    df.columns = df.columns.astype(str).str.strip().str.strip(",").str.strip()
    df.columns = [c.strip() for c in df.columns]

    # 3. Vérifier que les colonnes attendues existent
    print("COLONNES DETECTEES :", list(df.columns))

    # Si la 1ère colonne s'appelle "text," ou autre, on la renomme
    df = df.rename(columns={df.columns[0]: "text", df.columns[1]: "sentiment"})

    # 4. Nettoyer les valeurs
    df["text"] = df["text"].astype(str).str.strip()
    df["sentiment"] = df["sentiment"].astype(str).str.strip().str.upper()

    # 5. Filtrer les sentiments valides
    df = df[df["sentiment"].isin(["POSITIVE", "NEGATIVE", "NEUTRAL"])]

    print(f"NOMBRE D'AVIS : {len(df)}")

    y_true = df["sentiment"].tolist()
    y_pred = []
    latences = []

    for text in df["text"]:
        start = time.time()
        res = mon_ia(text)
        end = time.time()
        y_pred.append(res["sentiment"])
        latences.append(end - start)

    precision = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    
    print(f"Precision : {precision:.2%}")
    

    assert precision > 0.80