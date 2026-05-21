import os
# On garde uniquement Google (et Twitter si besoin)
from google_collector import chercher_avis_google

def collecter_partout(mot_cle, limite=10):
    """
    Collecte les avis UNIQUEMENT depuis internet (Google, Twitter)
    Plus aucun fichier CSV local !
    """
    print(f"--- Lancement de la collecte en ligne pour : {mot_cle} ---")
    
    resultats_finaux = {
        "google": [],
        "twitter": [],   # Tu pourras ajouter Twitter plus tard
        "total": 0
    }
    
    # 1. Collecte sur Google (web)
    try:
        print("🔍 Recherche sur Google...")
        avis_web = chercher_avis_google(mot_cle, limite)
        resultats_finaux["google"] = avis_web
        print(f"✅ {len(avis_web)} résultats trouvés sur Google")
    except Exception as e:
        print(f"❌ Erreur sur Google : {e}")
    
    # 2. Optionnel : Twitter 
    #     from twitter_collector import collecter_tweets
    #     print("🐦 Recherche sur Twitter...")
    #     tweets = collecter_tweets(mot_cle, limite)
    #     resultats_finaux["twitter"] = tweets
    # except Exception as e:
    #     print(f"Twitter indisponible : {e}")
    
    # 3. Calcul du total
    total = len(resultats_finaux["google"]) + len(resultats_finaux["twitter"])
    resultats_finaux["total"] = total
    
    print(f"--- ✅ Collecte terminée ! {total} avis récupérés depuis le web ---")
    return resultats_finaux