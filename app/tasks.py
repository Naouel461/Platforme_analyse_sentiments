from celery import Celery
import os

# Configuration de base pour se connecter à Redis
# On utilise une adresse simple par défaut
adresse_redis = "redis://localhost:6379/0"

# Création de l'application Celery
mon_app = Celery('mes_taches', broker=adresse_redis)

# Option simple pour les résultats
mon_app.conf.result_backend = adresse_redis

@mon_app.task
def analyser_texte_tache(texte):
    """ Tâche pour lancer l'analyse en arrière-plan """
    # On simule un résultat pour le moment
    print("Analyse en cours pour :", texte)
    return {
        "texte": texte, 
        "sentiment": "positif", 
        "score": 0.90
    }

@mon_app.task
def collecter_donnees_tache(mot_cle, site="google"):
    """ Tâche pour récupérer des données sur internet """
    print(f"Lancement de la recherche pour {mot_cle} sur {site}")
    return {
        "mot_cle": mot_cle, 
        "site": site, 
        "etat": "termine"
    }
