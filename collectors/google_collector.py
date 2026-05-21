import requests
import os

def chercher_avis_google(mot_cle, limite=10):
    """
    Utilise l'API Google Custom Search (gratuit 100 requêtes/jour)
    """
    API_KEY = os.getenv("GOOGLE_API_KEY", "ta_clé_ici")
    CX_ID = os.getenv("GOOGLE_CX_ID", "ton_moteur_id")  # À créer sur Google Cloud
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': API_KEY,
        'cx': CX_ID,
        'q': f"{mot_cle} avis",
        'hl': 'fr',
        'num': limite
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        resultats = []
        for item in data.get('items', []):
            resultats.append({
                "titre": item.get('title'),
                "description": item.get('snippet'),
                "lien": item.get('link'),
                "date_collecte": datetime.now().strftime("%Y-%m-%d"),
                "source": "Google Custom Search"
            })
        
        print(f"✅ {len(resultats)} résultats via API Google")
        return resultats
        
    except Exception as e:
        print(f"❌ Erreur API : {e}")
        return []