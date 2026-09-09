"""
TEST DE PERFORMANCE - À EXÉCUTER DIRECTEMENT
Ne pas utiliser avec pytest !
Exécution: python tests/performance_test.py
"""

import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import statistics

BASE_URL = "http://localhost:8002"

# Données de test
TEXTS = [
    "Ce produit est excellent !",
    "Service client horrible", 
    "Bon rapport qualité prix",
    "Je suis très satisfait",
    "Déçu par la qualité",
    "Produit correct sans plus",
    "Je recommande vivement",
    "Très mauvais service",
    "Qualité exceptionnelle",
    "Ne répond pas aux attentes",
    "Super expérience",
    "À éviter absolument",
    "Rapport qualité-prix imbattable",
    "Déception totale",
    "Très bonne surprise",
    "Médiocre",
    "Parfait",
    "À améliorer",
    "Excellent rapport qualité-prix",
    "Je ne recommande pas"
]

def test_predict(text):
    """Test une prédiction"""
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/test-sentiment",
            json={"text": text},
            timeout=30
        )
        elapsed = time.time() - start
        return {
            "success": response.status_code == 200,
            "time": elapsed,
            "status": response.status_code,
            "text": text[:30],
            "result": response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {
            "success": False,
            "time": time.time() - start,
            "error": str(e),
            "text": text[:30]
        }

def run_performance_test(concurrent=10, total_requests=100):
    """Exécute un test de performance"""
    print("=" * 70)
    print("🚀 TEST DE PERFORMANCE")
    print(f"📊 {total_requests} requêtes, {concurrent} concurrentes")
    print("=" * 70)
    
    results = []
    start_time = time.time()
    
    # Préparer les requêtes
    texts = TEXTS * (total_requests // len(TEXTS) + 1)
    texts = texts[:total_requests]
    
    # Exécuter avec ThreadPool
    print(f"\n⏳ Exécution de {total_requests} requêtes...")
    with ThreadPoolExecutor(max_workers=concurrent) as executor:
        futures = [executor.submit(test_predict, text) for text in texts]
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)
            if (i + 1) % 10 == 0:
                print(f"   {i+1}/{total_requests} requêtes terminées")
    
    total_time = time.time() - start_time
    
    # Statistiques
    success = sum(1 for r in results if r.get("success", False))
    times = [r.get("time", 0) for r in results if r.get("success", False)]
    
    print(f"\n📈 RÉSULTATS:")
    print(f"  ✅ Succès: {success}/{total_requests} ({success/total_requests*100:.1f}%)")
    print(f"  ❌ Échecs: {total_requests - success}")
    print(f"  ⏱️ Temps total: {total_time:.2f}s")
    print(f"  ⏱️ Temps moyen: {statistics.mean(times):.3f}s" if times else "  ⏱️ Temps moyen: N/A")
    print(f"  🚀 Requêtes/sec: {total_requests/total_time:.1f}")
    
    # Distribution des temps
    if times:
        print(f"\n📊 Distribution des temps:")
        print(f"  Min: {min(times):.3f}s")
        print(f"  Max: {max(times):.3f}s")
        print(f"  Médiane: {statistics.median(times):.3f}s")
        print(f"  Écart-type: {statistics.stdev(times):.3f}s" if len(times) > 1 else "")
    
    # Erreurs
    errors = [r for r in results if not r.get("success", False)]
    if errors:
        print(f"\n❌ Erreurs ({len(errors)}):")
        for err in errors[:5]:
            print(f"  - {err.get('text', '')}: {err.get('error', 'Unknown')}")
    
    # Résultats des prédictions
    sentiments = []
    for r in results:
        if r.get("success") and r.get("result"):
            sentiment = r["result"].get("sentiment", "UNKNOWN")
            sentiments.append(sentiment)
    
    if sentiments:
        print(f"\n📊 Distribution des sentiments:")
        unique = list(set(sentiments))
        for s in unique:
            count = sentiments.count(s)
            print(f"  {s}: {count} ({count/len(sentiments)*100:.1f}%)")
    
    # Sauvegarder le rapport
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_requests": total_requests,
        "concurrent": concurrent,
        "success": success,
        "failed": total_requests - success,
        "total_time": total_time,
        "avg_time": statistics.mean(times) if times else 0,
        "requests_per_sec": total_requests/total_time,
        "min_time": min(times) if times else 0,
        "max_time": max(times) if times else 0,
        "median_time": statistics.median(times) if times else 0
    }
    
    with open("performance_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Rapport sauvegardé: performance_report.json")
    print("=" * 70)
    
    return report

def test_sequential_latency():
    """Test de latence séquentielle"""
    print("\n" + "=" * 70)
    print("⏱️ TEST DE LATENCE SÉQUENTIELLE")
    print("=" * 70)
    
    times = []
    for i, text in enumerate(TEXTS[:10]):
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/test-sentiment",
                json={"text": text},
                timeout=10
            )
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  {i+1}. {text[:30]:30s} → {elapsed:.3f}s")
        except Exception as e:
            print(f"  {i+1}. {text[:30]:30s} → ERREUR: {e}")
    
    if times:
        print(f"\n📊 Statistiques:")
        print(f"  Moyenne: {statistics.mean(times):.3f}s")
        print(f"  Min: {min(times):.3f}s")
        print(f"  Max: {max(times):.3f}s")
        print(f"  Médiane: {statistics.median(times):.3f}s")
        print(f"  Écart-type: {statistics.stdev(times):.3f}s" if len(times) > 1 else "")
    
    print("=" * 70)

# ============================================
# POINT D'ENTRÉE - Exécution directe
# ============================================

if __name__ == "__main__":
    print("\n🔬 SUITE DE TESTS DE PERFORMANCE")
    print("=" * 70)
    
    # Test séquentiel de latence
    test_sequential_latency()
    
    print("\n\n")
    
    # Test avec différents niveaux de charge
    tests = [
        (2, 10, "Léger"),
        (5, 50, "Moyen"),
        (10, 100, "Lourd")
    ]
    
    for concurrent, total, level in tests:
        print(f"\n\n{level.upper()} - {concurrent} concurrents, {total} requêtes")
        run_performance_test(concurrent=concurrent, total_requests=total)
        time.sleep(2)  # Pause entre les tests
    
    print("\n" + "=" * 70)
    print("✅ TOUS LES TESTS DE PERFORMANCE TERMINÉS")
    print("=" * 70)