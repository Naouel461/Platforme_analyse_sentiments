from transformers import pipeline as pipe

# Chargement des modèles
try:
    f_model = pipe("sentiment-analysis", model="camembert/camembert-base-sentiment")
    a_model = pipe("sentiment-analysis", model="aubmindlab/bert-base-arabertv02-twitter-sentiment")
    print("ok")
except:
    print("erreur")

def get_lang(s):
    # Compte les caractères arabes
    c = 0
    for char in s:
        if 0x0600 <= ord(char) <= 0x06FF:
            c += 1
    if c > (len(s) * 0.2):
        return 'ar'
    else:
        return 'fr'

def backup(t):
    # Analyse de secours par mots-clés
    t = t.lower()
    p = ['bon', 'super', 'bien', 'رائع', 'جيد']
    m = ['nul', 'mauvais', 'pire', 'سيء', 'رديء']
    v = 0
    for x in p:
        if x in t: v += 1
    for x in m:
        if x in t: v -= 1
        
    if v > 0: 
        return "POSITIVE", 0.6
    elif v < 0:
        return "NEGATIVE", 0.6
    else:
        return "NEUTRAL", 0.5

def mon_ia(txt):
    # Vérification longueur
    if not txt or len(txt) < 3:
        return {"sentiment": "NEUTRE", "score": 0}
        
    l = get_lang(txt)
    try:
        # Lancement de l'analyse
        if l == 'fr': 
            res = f_model(txt)[0]
        else: 
            res = a_model(txt)[0]
            
        lab = res['label'].upper()
        
        # Gestion des modèles à étoiles (Stars)
        if 'STAR' in lab:
            n = int(''.join(filter(str.isdigit, lab)))
            if n <= 2: 
                lab = "NEGATIVE"
            elif n >= 4: 
                lab = "POSITIVE"
            else: 
                lab = "NEUTRAL"
                
        return {
            "sentiment": lab, 
            "confiance": round(res['score'], 2), 
            "lang": l
        }
    except:
        # Si le modèle plante, on utilise le backup
        s, c = backup(txt)
        return {"sentiment": s, "confiance": c, "lang": "error"}
