from locust import HttpUser, task, between
import random

class SentimentTestUser(HttpUser):
    # Attendre 1-3 secondes entre chaque test
    wait_time = between(1, 3)
    
    def on_start(self):
        """Appelé au démarrage"""
        print("🧪 Début des tests de charge...")
    
    @task(4)
    def test_predict(self):
        """Test le plus fréquent : analyse simple"""
        texts = [
            "Ce produit est excellent !",
            "Service client médiocre",
            "Bon rapport qualité prix",
            "Je suis très satisfait",
            "Déçu par la qualité",
            "Produit correct sans plus",
        ]
        self.client.post("/test-sentiment", json={
            "text": random.choice(texts)
        })
    
    @task(2)
    def get_stats(self):
        """Récupère les stats"""
        self.client.get("/stats")
    
    @task(2)
    def get_history(self):
        """Récupère l'historique"""
        self.client.get("/historique?limit=20")
    
    @task(1)
    def health_check(self):
        """Vérifie que l'API est vivante"""
        self.client.get("/")
    
    @task(1)
    def recherche_mock(self):
        """Test de recherche avec données mock (pas Google)"""
        self.client.get("/test-recherche-mock?mot_cle=restaurant&limit=3")