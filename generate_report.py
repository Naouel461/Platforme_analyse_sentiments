import json

def main():
    with open('data/processed/sentiments.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    positif = sum(1 for d in data if d.get('sentiment') == 'positif')
    negatif = sum(1 for d in data if d.get('sentiment') == 'negatif')
    neutre = sum(1 for d in data if d.get('sentiment') == 'neutre')
    
    print(f"Rapport d'analyse des sentiments")
    print(f"Total tweets: {len(data)}")
    print(f"Positifs: {positif}")
    print(f"Négatifs: {negatif}")
    print(f"Neutres: {neutre}")
    
    # Sauvegarder le rapport
    report = {
        "total": len(data),
        "positif": positif,
        "negatif": negatif,
        "neutre": neutre
    }
    
    with open('data/processed/report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
