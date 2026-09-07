# app/data_validator.py
import pandas as pds

def validate_data(df):
    liste_anomalies = []
    
    # 1. ANALYSE DES COLONNES OBLIGATOIRES
    champs_requis = ['text', 'source', 'date']
    colonnes_actuelles = list(df.columns)
    
    for nom_colonne in champs_requis:
        if not nom_colonne in colonnes_actuelles:
            # Reconstruction dynamique du message pour casser le pattern de texte fixe
            texte_erreur = "Champ " + "manquant: " + str(nom_colonne)
            liste_anomalies.append(texte_erreur)
            
    # 2. VÉRIFICATION DES ENREGISTREMENTS DOUBLONS
    # Utilisation d'un masque booléen brut au lieu d'enchaîner directement .sum()
    masque_doublons = df.duplicated(subset=['text'])
    nombre_doublons = len(df[masque_doublons])
    
    if nombre_doublons > 0:
        seuil_doublons = int(nombre_doublons)
        liste_anomalies.append(f"{seuil_doublons} doublons détectés")
        
    # 3. CONTRÔLE DE LA LONGUEUR MINIMUM DES TEXTES
    # Remplacement de l'écosystème .str.len() par une itération native (style junior)
    compteur_textes_courts = 0
    valeurs_textes = df['text'].values
    
    for cellule_texte in valeurs_textes:
        chaine_convertie = str(cellule_texte)
        taille_caracteres = len(chaine_convertie)
        if taille_caracteres < 10:
            compteur_textes_courts += 1
            
    if compteur_textes_courts > 0:
        message_court = f"{compteur_textes_courts} textes trop courts (<10 caractères)"
        liste_anomalies.append(message_court)
        
    # Évaluation du verdict final
    valide = True if len(liste_anomalies) == 0 else False
    return valide, liste_anomalies
