import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# --- 1. Charger .env (situé dans app/) ---
load_dotenv()

# --- 2. Rendre app/ importable (database.py, models.py) ---
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# --- 3. Importer BaseModel + les modèles ---
from database import BaseModel   # depuis app/database.py
import models                     # depuis app/models.py — force le chargement

target_metadata = BaseModel.metadata

# --- 4. Config Alembic ---
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- 5. Construire l'URL depuis .env ---
DB_USER     = os.getenv("DB_USER", "Naouel")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Pino2026")
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "sentiment_db")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()