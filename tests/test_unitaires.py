import pytest
from unittest.mock import patch, MagicMock
import json

from app.main import hash_password, verify_password, save_search_and_predictions, get_db_connection
from app.sentiment_analyzer import mon_ia
from app.etl_pipeline import nettoyer_mon_texte

# --- 1. Tests de securite ---
def test_hash_password():
    pwd = "MonMotDePasse123!"
    h = hash_password(pwd)
    assert h != pwd
    assert "$" in h
    assert len(h) > 20


def test_verify_password():
    pwd = "MonMotDePasse123!"
    h = hash_password(pwd)
    assert verify_password(pwd, h) is True
    assert verify_password("mauvais", h) is False
    assert verify_password("", h) is False

# --- 2. Tests du modele BERT (mon_ia) ---
def test_mon_ia_positif():
    res = mon_ia("Ce produit est excellent, je recommande !")
    assert res["sentiment"] == "POSITIVE"
    assert 0 <= res["confiance"] <= 1

def test_mon_ia_negatif():
    res = mon_ia("Vraiment decu, service nul.")
    assert res["sentiment"] == "NEGATIVE"
    assert 0 <= res["confiance"] <= 1

def test_mon_ia_vide():
    res = mon_ia("")
    assert res["sentiment"] == "NEUTRAL"
    assert res["confiance"] == 0
    assert res["lang"] == "unknown"
def test_mon_ia_court():
    res = mon_ia("ok")
    assert res["sentiment"] == "NEUTRAL"


# --- 3. Tests du pipeline ETL ---
def test_nettoyer_texte_nan():
    assert nettoyer_mon_texte("nan", "fr") == ""


def test_nettoyer_texte_minuscules():
    assert nettoyer_mon_texte("BONJOUR", "fr") == "bonjour"


def test_nettoyer_texte_liens():
    texte = "Visitez https://example.com et www.test.com"
    assert "http" not in nettoyer_mon_texte(texte, "fr")
    assert "www" not in nettoyer_mon_texte(texte, "fr")


def test_nettoyer_texte_ponctuation():
    texte = "Bonjour, comment ca va ?"
    result = nettoyer_mon_texte(texte, "fr")
    assert "," not in result
    assert "?" not in result
