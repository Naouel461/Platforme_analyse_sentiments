import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# --- Variables de connexion ---
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "sentiment_db")
DB_USER     = os.getenv("DB_USER", "Naouel")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Pino2026")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- Moteur et session SQLAlchemy ---
moteur_db = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocale = sessionmaker(bind=moteur_db, autoflush=False, autocommit=False)

# --- Base déclarative (les modèles hériteront de cette classe) ---
BaseModel = declarative_base()


# --- Dépendance FastAPI ---
def get_db():
    db = SessionLocale()
    try:
        yield db
    finally:
        db.close()