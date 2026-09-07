# J'importe les trucs pour la base de données
import sqlalchemy as sql
import os
from dotenv import load_dotenv

# Je lance le chargement de mon petit fichier .env
load_dotenv()

# --- MES VARIABLES DE CONNEXION ---
# Je les récupère une par une pour être sûr
hote_db = os.getenv("DB_HOST", "db")
port_du_serveur = os.getenv("DB_PORT", "5432")
nom_de_ma_bdd = os.getenv("DB_NAME", "sentiment_db")
mon_login = os.getenv("DB_USER", "Naouel")
mon_mot_de_passe = os.getenv("DB_PASSWORD", "Pino2026")

# Petit print pour vérifier si ça marche (je le commenterai après)
# print("Connexion en cours sur :", hote_db)

# Fabrication du lien pour SQLAlchemy (un peu long mais ça marche)
chaine_finale = "postgresql://" + mon_login + ":" + mon_mot_de_passe
chaine_finale += "@" + hote_db + ":" + port_du_serveur + "/" + nom_de_ma_bdd

# Création du moteur de recherche
moteur_db = sql.create_engine(chaine_finale)

# Je configure ma session ici
from sqlalchemy.orm import sessionmaker as createur_session
SessionLocale = createur_session(bind=moteur_db)

# La base pour mes futures classes
from sqlalchemy.ext.declarative import declarative_base
BaseModel = declarative_base()

# La fonction magique pour ouvrir/fermer la db
def get_db():
    ma_session_ouverte = SessionLocale()
    try:
        # Je renvoie la session pour qu'on puisse l'utiliser
        yield ma_session_ouverte
    finally:
        # Toujours bien fermer la porte à la fin !
        ma_session_ouverte.close()
