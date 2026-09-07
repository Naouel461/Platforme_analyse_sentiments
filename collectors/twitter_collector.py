import snscrape.modules.twitter as sntwitter
from datetime import datetime

def collecter_tweets(mot_cle, limite=10):
    """
    Cette fonction utilise snscrape pour trouver des tweets 
    récents sur un sujet précis.
    """
    print(f"--- Recherche de tweets pour : {mot_cle} ---")
    
    liste_tweets = []
    
    # On prépare la requête (on cherche en français)
    requete = f"{mot_cle} lang:fr"

    try:
        # On utilise le scraper de snscrape pour parcourir Twitter
        scraper = sntwitter.TwitterSearchScraper(requete)
        
        for i, tweet in enumerate(scraper.get_items()):
            # On s'arrête quand on a assez de résultats
            if i >= limite:
                break
                
            # On récupère les infos importantes du tweet
            infos = {
                'texte': tweet.content,
                'utilisateur': tweet.user.username,
                'date': tweet.date.strftime("%Y-%m-%d"),
                'lien': tweet.url,
                'likes': tweet.likeCount,
                'source': 'Twitter'
            }
            liste_tweets.append(infos)
            
        print(f"Succès : {len(liste_tweets)} tweets récupérés.")
        return liste_tweets

    except Exception as e:
        print("Oups, petit souci avec Twitter :", e)
        # Si ça ne marche pas, on renvoie une liste vide pour ne pas faire planter le programme
        return []

