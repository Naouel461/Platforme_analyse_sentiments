import pandas as pd

# Ici, je crée mes propres listes de mots qui ne servent à rien pour l'analyse
# On les appelle les "stop words"
mots_inutiles_fr = ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car', 'que', 'qui', 'quoi', 'dont', 'où', 'est', 'sont', 'a', 'ont', 'pour', 'par', 'avec', 'en', 'dans']
mots_inutiles_ar = ['من', 'في', 'على', 'إلى', 'مع', 'هذا', 'هذه', 'كان', 'و', 'أو', 'ثم', 'يا', 'ب']

def verifier_emojis_complet(texte):
    """
    Cette fonction parcourt le texte pour trouver tous les emojis
    et calcule si le message est plutôt joyeux ou triste.
    """
    score = 0
    emojis_trouves = []
    
    for caractere in texte:
        # Je récupère le code de la lettre ou du symbole
        code = ord(caractere)
        
        # Les emojis ont des codes très grands (au-dessus de 10000)
        # Je vérifie s'ils appartiennent aux familles de smileys ou drapeaux
        est_un_emoji = (
            (0x1F600 <= code <= 0x1F64F) or 
            (0x1F300 <= code <= 0x1F5FF) or 
            (0x1F680 <= code <= 0x1F6FF) or 
            (0x2600 <= code <= 0x26FF)   or 
            (0x1F1E0 <= code <= 0x1F1FF)
        )
        
        if est_un_emoji:
            emojis_trouves.append(caractere)
            # Si c'est un emoji sympa, on ajoute des points
            if caractere in ['😊', '😁', '👍', '❤️', '😍']:
                score = score + 0.1
            # Si c'est un emoji pas content, on enlève des points
            elif caractere in ['😡', '👎', '💀', '😢', '😭']:
                score = score - 0.1
            else:
                # Sinon c'est un objet ou un drapeau, ça compte pour 0
                score = score + 0 
                
    return emojis_trouves, score

def nettoyer_mon_texte(texte, langue):
    """
    Sert à nettoyer le texte : enlever les majuscules, les liens web 
    et toute la ponctuation inutile.
    """
    # Si la case est vide dans Excel/CSV, on retourne un texte vide
    if str(texte) == "nan":
        return ""
    
    # On met tout en minuscules pour ne pas avoir de différences
    texte = texte.lower()
    
    # Pour enlever les liens, je coupe le texte en mots
    mots = texte.split()
    liste_sans_liens = []
    for m in mots:
        # Si le mot contient http ou www, c'est un lien, donc je l'ignore
        if "http" not in m and "www" not in m:
            liste_sans_liens.append(m)
    
    # Je recolle les mots propres ensemble
    texte_propre = " ".join(liste_sans_liens)
    
    # Ici j'enlève les points, virgules, etc. un par un
    ponctuation = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    propre_final = ""
    for lettre in texte_propre:
        if lettre not in ponctuation:
            propre_final = propre_final + lettre
            
    return propre_final.strip()

def enlever_mots_vides(texte, langue):
    """
    Supprime les petits mots de liaison (le, la, de...)
    """
    mots = texte.split()
    if langue == "fr":
        liste_reference = mots_inutiles_fr
    else:
        liste_reference = mots_inutiles_ar
        
    mots_gardes = []
    for m in mots:
        # On ne garde le mot que s'il n'est pas dans notre liste de mots inutiles
        if m not in liste_reference:
            mots_gardes.append(m)
            
    return " ".join(mots_gardes)

def extraire_stats(texte):
    """
    Calcule des statistiques simples : nombre de mots, longueur, etc.
    """
    # On compte les lettres et les mots
    nb_lettres = len(texte)
    mots = texte.split()
    nb_mots = len(mots)
    
    # Calcul de la moyenne (attention à ne pas diviser par zéro !)
    if nb_mots > 0:
        moyenne = nb_lettres / nb_mots
    else:
        moyenne = 0
        
    # On récupère aussi les infos sur les emojis
    liste_emo, score_emo = verifier_emojis_complet(texte)
    
    # Petit test pour voir s'il y a beaucoup de MAJUSCULES (colère ?)
    majuscules = 0
    for c in texte:
        if c.isupper():
            majuscules = majuscules + 1
            
    return nb_lettres, nb_mots, moyenne, len(liste_emo), score_emo, majuscules

def supprimer_doublons(df, nom_colonne):
    """
    Supprime les lignes identiques dans le tableau
    """
    return df.drop_duplicates(subset=[nom_colonne])

def separer_train_test(df):
    """
    Mélange les données et les coupe en deux parties : 
    80% pour l'entraînement et 20% pour le test.
    """
    # Je mélange les lignes au hasard
    df_aleatoire = df.sample(frac=1).reset_index(drop=True)
    
    # Je calcule l'endroit où couper
    limite = int(len(df_aleatoire) * 0.8)
    
    # Je sépare le tableau en deux
    train = df_aleatoire.iloc[:limite]
    test = df_aleatoire.iloc[limite:]
    
    return train, test
