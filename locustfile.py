from locust import HttpUser, task, between
import random

class SentimentUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def test_sentiment(self):
        """Test d'analyse de sentiment"""
        texts = [
            "Ce produit est excellent !",
            "Service client horrible",
            "Qualité moyenne, sans plus",
            "Je recommande vivement !",
            "Très déçu par ce service"
        ]
        text = random.choice(texts)
        self.client.post("/test-sentiment", json={"text": text})

    @task(2)
    def search_reviews(self):
        """Test de recherche d'avis"""
        keywords = ["Mytek", "Boga", "Spacenet", "Mokito"]
        keyword = random.choice(keywords)
        self.client.get(f"/recherche_avis?mot_cle={keyword}%2C%20Tunisie&limit=5")

    @task(1)
    def get_stats(self):
        """Test des statistiques"""
        self.client.get("/stats")

    @task(1)
    def get_history(self):
        """Test de l'historique"""
        self.client.get("/historique?limit=10")