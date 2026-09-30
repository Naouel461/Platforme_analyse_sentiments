from locust import HttpUser, task, between

class SentimentAnalysisUser(HttpUser):
    # Temps d'attente entre les requêtes (1 à 5 secondes)
    wait_time = between(1, 5)

    @task
    def test_root(self):
        self.client.get("/")

    @task(2)
    def test_stats(self):
        self.client.get("/stats")

    @task(3)
    def test_sentiment(self):
        # Exemple de payload correspondant à votre route POST /test-sentiment
        payload = {"text": "Excellent produit, j'adore l'interface !"}
        self.client.post("/test-sentiment", json=payload)
