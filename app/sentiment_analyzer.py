import torch
from transformers import pipeline

print("🚀 Worker - Chargement du modèle BERT multilingue...")

device = 0 if torch.cuda.is_available() else -1
classifier = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    device=device,
    truncation=True,
    max_length=512
)
print("✅ Modèle BERT chargé avec succès")

def mon_ia(txt):
    """Analyse le sentiment avec BERT"""
    if not txt or not isinstance(txt, str) or len(txt.strip()) < 3:
        return {"sentiment": "NEUTRAL", "confiance": 0, "lang": "unknown"}

    try:
        result = classifier(txt)[0]
        label = result['label']          # ex: "5 stars"
        stars = int(label.split()[0])    # 1 à 5
        score = (stars - 3) / 2          # transforme en -1..1
        confidence = abs(score)

        if score > 0.2:
            sentiment = "POSITIVE"
        elif score < -0.2:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"

        return {
            "sentiment": sentiment,
            "confiance": round(confidence, 2),
            "lang": "multi"
        }
    except Exception as e:
        print(f"⚠️ Erreur analyse: {e}")
        return {"sentiment": "NEUTRAL", "confiance": 0, "lang": "unknown"}

def analyze_sentiment(text):
    result = mon_ia(text)
    return {"sentiment": result["sentiment"].lower(), "confidence": result["confiance"]}