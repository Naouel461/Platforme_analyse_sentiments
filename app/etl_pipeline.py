# ============================================================
# FICHIER : app/etl_pipeline.py
# RÔLE : Pipeline ETL (Extract, Transform, Load)
# CORRECTIONS : Encodage UTF-8 + filtrage des colonnes
# ============================================================

import pandas as pd

# ============================================================
# MOTS INUTILES (STOP WORDS)
# ============================================================
mots_inutiles_fr = [
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
    'mais', 'donc', 'or', 'ni', 'car', 'que', 'qui', 'quoi', 'dont',
    'où', 'est', 'sont', 'a', 'ont', 'pour', 'par', 'avec', 'en', 'dans'
]
mots_inutiles_ar = ['من', 'في', 'على', 'إلى', 'مع', 'هذا', 'هذه', 'كان', 'و', 'أو', 'ثم', 'يا', 'ب']


# ============================================================
# FONCTION 1 : VÉRIFICATION DES EMOJIS
# ============================================================
def verifier_emojis_complet(texte):
    """
    Parcourt le texte pour trouver les emojis et calcule
    si le message est plutôt joyeux ou triste.
    """
    score = 0
    emojis_trouves = []

    for caractere in texte:
        code = ord(caractere)

        # Les emojis ont des codes très grands (au-dessus de 10000)
        est_un_emoji = (
            (0x1F600 <= code <= 0x1F64F) or
            (0x1F300 <= code <= 0x1F5FF) or
            (0x1F680 <= code <= 0x1F6FF) or
            (0x2600 <= code <= 0x26FF) or
            (0x1F1E0 <= code <= 0x1F1FF)
        )

        if est_un_emoji:
            emojis_trouves.append(caractere)
            if caractere in ['😊', '😁', '👍', '❤️', '😍']:
                score += 0.1
            elif caractere in ['😡', '👎', '💀', '😢', '😭']:
                score -= 0.1

    return emojis_trouves, score


# ============================================================
# FONCTION 2 : NETTOYAGE DU TEXTE
# ============================================================
def nettoyer_mon_texte(texte, langue):
    """
    Nettoie le texte :
    - Corrige l'encodage UTF-8 cassé (Ã© → é)
    - Met en minuscules
    - Retire les liens web
    - Retire la ponctuation
    """
    if str(texte) == "nan":
        return ""

    # 🔑 CORRECTION ENCODAGE (Ã© → é, Ã¨ → è, etc.)
    try:
        texte = str(texte).encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        texte = str(texte)

    # Mettre en minuscules
    texte = texte.lower()

    # Retirer les liens
    mots = texte.split()
    liste_sans_liens = [m for m in mots if "http" not in m and "www" not in m]
    texte_propre = " ".join(liste_sans_liens)

    # Retirer la ponctuation
    ponctuation = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    propre_final = ""
    for lettre in texte_propre:
        if lettre not in ponctuation:
            propre_final = propre_final + lettre

    return propre_final.strip()


# ============================================================
# FONCTION 3 : RETIRER LES MOTS VIDES
# ============================================================
def enlever_mots_vides(texte, langue):
    """
    Supprime les mots de liaison (le, la, de...)
    """
    mots = texte.split()
    liste_reference = mots_inutiles_fr if langue == "fr" else mots_inutiles_ar
    mots_gardes = [m for m in mots if m not in liste_reference]
    return " ".join(mots_gardes)


# ============================================================
# FONCTION 4 : EXTRAIRE LES STATISTIQUES
# ============================================================
def extraire_stats(texte):
    """
    Calcule des statistiques simples : nombre de mots, longueur, etc.
    """
    nb_lettres = len(texte)
    mots = texte.split()
    nb_mots = len(mots)

    moyenne = nb_lettres / nb_mots if nb_mots > 0 else 0

    liste_emo, score_emo = verifier_emojis_complet(texte)

    majuscules = sum(1 for c in texte if c.isupper())

    return nb_lettres, nb_mots, moyenne, len(liste_emo), score_emo, majuscules


# ============================================================
# FONCTION 5 : SUPPRIMER LES DOUBLONS
# ============================================================
def supprimer_doublons(df, nom_colonne):
    """Supprime les lignes identiques dans le tableau."""
    return df.drop_duplicates(subset=[nom_colonne])


# ============================================================
# FONCTION 6 : SÉPARER TRAIN/TEST (utilisée par data_splitter.py)
# ============================================================
def separer_train_test(df):
    """
    Mélange les données et les coupe en deux parties :
    80% pour l'entraînement et 20% pour le test.
    """
    df_aleatoire = df.sample(frac=1).reset_index(drop=True)
    limite = int(len(df_aleatoire) * 0.8)
    train = df_aleatoire.iloc[:limite]
    test = df_aleatoire.iloc[limite:]
    return train, test


# ============================================================
# POINT D'ENTRÉE POUR DVC
# ============================================================
if __name__ == "__main__":
    import os
    import json
    import pandas as pd

    print("🚀 [ETL] Démarrage du pipeline...")

    raw_dir = "data/raw"
    if not os.path.exists(raw_dir):
        print(f"❌ [ETL] Dossier {raw_dir} introuvable")
        exit(1)

    # 🔑 Ne lire que les fichiers qui contiennent du TEXTE à analyser
    # (exclut searches.json qui contient des mots-clés, pas des textes)
    raw_files = [
        f for f in os.listdir(raw_dir)
        if f.endswith('.json')
        and f in ['predictions.json', 'feedbacks.json', 'reviews.json']
    ]
    print(f"[ETL] {len(raw_files)} fichier(s) JSON : {raw_files}")

    all_data = []
    for f in raw_files:
        filepath = os.path.join(raw_dir, f)
        with open(filepath, 'r', encoding='utf-8-sig') as fh:
            try:
                content = json.load(fh)
                if isinstance(content, list):
                    for item in content:
                        item['_source_file'] = f
                        all_data.append(item)
                else:
                    content['_source_file'] = f
                    all_data.append(content)
                print(f"[ETL] ✅ {f} : {len(content)} enregistrements")
            except Exception as e:
                print(f"[ETL] ⚠️ Erreur {f}: {e}")

    print(f"[ETL] Total : {len(all_data)} enregistrements")

    if len(all_data) == 0:
        print("❌ [ETL] Aucune donnée")
        exit(1)

    # Créer le DataFrame
    df = pd.DataFrame(all_data)
    print(f"[ETL] Shape avant nettoyage : {df.shape}")

    # 🔑 Garder uniquement les colonnes utiles
    colonnes_utiles = ['id', 'text', 'sentiment', 'score', 'language',
                       'source', 'date', 'origin', 'rating', '_source_file']
    colonnes_presentes = [c for c in colonnes_utiles if c in df.columns]
    df = df[colonnes_presentes]
    print(f"[ETL] Colonnes filtrées : {list(df.columns)}")

    # 🔑 Nettoyer le texte
    if 'text' in df.columns:
        df = df.dropna(subset=['text'])
        df['text'] = df['text'].astype(str)

        try:
            df['text_clean'] = df['text'].apply(lambda x: nettoyer_mon_texte(x, 'fr'))
            df = df[df['text_clean'].str.len() >= 5]
        except Exception as e:
            print(f"[ETL] ⚠️ Nettoyage : {e}")

    print(f"[ETL] Shape après nettoyage : {df.shape}")

    # Sauvegarder
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/clean.csv", index=False)
    print(f"✅ [ETL] {len(df)} lignes → data/processed/clean.csv")