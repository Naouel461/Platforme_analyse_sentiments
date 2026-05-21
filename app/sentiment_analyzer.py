# sentiment_analyzer.py - Version FINALE avec modèle multilingue uniquement
from transformers import pipeline

print("🚀 Chargement du modèle multilingue...", flush=True)

# Utiliser uniquement le modèle multilingue qui fonctionne
modele_multilingue = None
try:
    modele_multilingue = pipeline(
        "sentiment-analysis", 
        model="nlptown/bert-base-multilingual-uncased-sentiment"
    )
    print("✅ Modèle multilingue chargé avec succès", flush=True)
except Exception as e:
    print(f"❌ Erreur chargement: {e}", flush=True)

print("Chargement terminé !", flush=True)

def detecter_langue(texte):
    """Détecte si le texte est en français ou arabe"""
    nb_arabe = sum(1 for c in texte if 0x0600 <= ord(c) <= 0x06FF)
    return 'ar' if nb_arabe > len(texte) * 0.2 else 'fr'

def analyser_mots_cles(texte, langue):
    """Analyse par mots-clés (fallback si modèle échoue)"""
    texte_lower = texte.lower()
    
    # Mots positifs
    positif_fr = ['genial', 'génial', 'super', 'excellent', 'parfait', 'formidable', 
                  'bon', 'bien', 'content', 'satisfait', 'ravi', 'heureux']
    positif_ar = ['رائع', 'ممتاز', 'جيد', 'جميل', 'مذهل']
    
    # Mots négatifs
    negatif_fr = ['nul', 'mauvais', 'horrible', 'déçu', 'decu', 'catastrophe', 
                  'déplorable', 'triste', 'dommage']
    negatif_ar = ['سيء', 'رديء', 'فظيع', 'محبط', 'كارثة']
    
    score = 0
    
    if langue == 'fr':
        for mot in positif_fr:
            if mot in texte_lower:
                score += 1
        for mot in negatif_fr:
            if mot in texte_lower:
                score -= 1
    else:
        for mot in positif_ar:
            if mot in texte:
                score += 1
        for mot in negatif_ar:
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

def convertir_label(label):
    """Convertit les labels du modèle multilingue (1-5 stars)"""
    if "1 star" in label or "2 star" in label:
        return "NEGATIVE"
    elif "4 star" in label or "5 star" in label:
        return "POSITIVE"
    else:
        return "NEUTRAL"

def mon_ia(texte):
    """Analyse le sentiment d'un texte"""
    if not texte or len(texte.strip()) < 3:
        return {"sentiment": "NEUTRAL", "confiance": 0.0, "lang": "unknown"}
    
    langue = detecter_langue(texte)
    print(f"  🔍 Analyse ({langue}): {texte[:50]}...", flush=True)
    
    # Essayer avec le modèle multilingue
    if modele_multilingue is not None:
        try:
            resultat = modele_multilingue(texte)[0]
            label_brut = resultat['label']
            score_brut = resultat['score']
            
            sentiment = convertir_label(label_brut)
            confiance = score_brut
            
            print(f"    📊 Modèle: {label_brut} -> {sentiment} ({confiance:.2f})", flush=True)
            
            # Si confiance faible, combiner avec mots-clés
            if confiance < 0.65:
                fb_sentiment, fb_confiance = analyser_mots_cles(texte, langue)
                print(f"    🔄 Fallback: {fb_sentiment} ({fb_confiance:.2f})", flush=True)
                
                if fb_confiance > confiance:
                    sentiment = fb_sentiment
                    confiance = (confiance + fb_confiance) / 2
                    
        except Exception as e:
            print(f"    ❌ Erreur: {e}, utilisation fallback", flush=True)
            sentiment, confiance = analyser_mots_cles(texte, langue)
    else:
        # Fallback si modèle non disponible
        sentiment, confiance = analyser_mots_cles(texte, langue)
    
    return {
        "sentiment": sentiment,
        "confiance": round(confiance, 2),
        "lang": langue
    }

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🧪 TEST DU MODÈLE MULTILINGUE")
    print("="*50)
    
    tests = [
        ("Ce produit est génial !", "POSITIVE"),
        ("Service horrible", "NEGATIVE"),
        ("Produit correct", "NEUTRAL"),
        ("منتج رائع جدا", "POSITIVE"),
        ("جودة سيئة جدا", "NEGATIVE"),
    ]
    
    for texte, expected in tests:
        resultat = mon_ia(texte)
        status = "✅" if resultat['sentiment'] == expected else "❌"
        print(f"{status} {resultat['sentiment']} (conf: {resultat['confiance']}) - {texte[:40]}")