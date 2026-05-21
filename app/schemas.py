from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Schéma pour envoyer un texte à l'IA
class EntreeTexte(BaseModel):
    texte: str

# Schéma pour demander une collecte de données
class RequeteCollecte(BaseModel):
    recherche: str
    limite: int = 10

# Schéma pour la réponse de l'analyse
class ReponseIA(BaseModel):
    texte: str
    resultat: str
    score: float

# Schéma pour l'historique enregistré dans la base
class HistoriqueAnalyse(BaseModel):
    id: int
    texte: str
    resultat: str
    score: float
    source: Optional[str] = "manuel"
    date_creation: datetime

    class Config:
        from_attributes = True