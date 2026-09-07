from sqlalchemy import Column, String, Integer, Float, Text
from database import BaseModel

class MesResultats(BaseModel):
    __tablename__ = "table_sentiments"
    
    # Cle primaire
    id = Column(Integer, primary_key=True)
    # Contenu du message
    phrase = Column(Text)
    # Classement final
    label = Column(String)
    # Score confiance
    valeur = Column(Float)
    # Source data
    origine = Column(String)
