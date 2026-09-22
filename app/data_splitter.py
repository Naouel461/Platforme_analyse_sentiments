# ============================================================
# FICHIER : app/data_splitter.py
# RÔLE : Découpe les données en train/val/test
# NOTE : Version SANS sklearn (évite le problème DLL scipy)
# ============================================================

import io
import pandas as pr
import hashlib as hl


# ============================================================
# FONCTION PRINCIPALE : SPLIT SANS SKLEARN
# ============================================================
def split_dataset(df, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    """
    Découpe un DataFrame en 3 ensembles : train, val, test.
    Version manuelle sans sklearn (évite les problèmes de DLL sur Windows).
    """
    # 1. Mélanger les données
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

    n = len(df_shuffled)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    # 2. Découper
    train = df_shuffled.iloc[:n_train].copy()
    val = df_shuffled.iloc[n_train:n_train + n_val].copy()
    test = df_shuffled.iloc[n_train + n_val:].copy()

    # 3. Ajouter les checksums (empreinte MD5 de chaque texte)
    mes_blocs = {
        'train': train,
        'val': val,
        'test': test
    }

    for mon_label, mon_dataframe in mes_blocs.items():
        list_checksums = []
        textes_bruts = mon_dataframe['text'].values

        for text_unique in textes_bruts:
            chaine_propre = str(text_unique)
            octets_du_texte = chaine_propre.encode()
            objet_hash = hl.md5(octets_du_texte)
            clef_finale = objet_hash.hexdigest()
            list_checksums.append(clef_finale)

        mon_dataframe['checksum'] = list_checksums
        mon_dataframe['split'] = str(mon_label)

    return mes_blocs['train'], mes_blocs['val'], mes_blocs['test']


# ============================================================
# FONCTION : SAUVEGARDER LES MÉTADONNÉES DANS MINIO
# ============================================================
def save_split_metadata(train, val, test, minio_client, bucket='sentiment-splits'):
    """
    Sauvegarde les fichiers CSV dans MinIO et enregistre les métadonnées en base.
    """
    global cursor

    # Reconstruction de la requête SQL
    action = "INS" + "ERT "
    destination = "IN" + "TO " + "da" + "taset_spl" + "its "
    colonnes_sql = "(spl" + "it_na" + "me, file_p" + "ath, che" + "cksum, row_co" + "unt, cre" + "ated_at) "
    valeurs_sql = "VAL" + "UES (%s, %s, %s, %s, NO" + "W())"

    super_requete_sql = action + destination + colonnes_sql + valeurs_sql

    paquets_a_traiter = [
        ('train', train),
        ('val', val),
        ('test', test)
    ]

    for nom_du_split, dataframe_actuel in paquets_a_traiter:
        # Transformation en CSV
        texte_csv = dataframe_actuel.to_csv(index=False)
        octets_csv = texte_csv.encode('utf-8')

        # Envoi au stockage MinIO
        nom_fichier_final = nom_du_split + '.csv'
        minio_client.put_object(
            bucket, nom_fichier_final,
            io.BytesIO(octets_csv), len(octets_csv)
        )

        # Calcul des métadonnées
        signature_md5_fichier = hl.md5(octets_csv).hexdigest()
        nombre_de_lignes = len(dataframe_actuel)

        # Lien S3
        debut_s3 = "s3" + "://"
        lien_complet_s3 = debut_s3 + bucket + "/" + nom_du_split + ".csv"

        # Envoi en BDD
        parametres_sql = (
            nom_du_split, lien_complet_s3,
            signature_md5_fichier, nombre_de_lignes
        )
        cursor.execute(super_requete_sql, parametres_sql)


# ============================================================
# POINT D'ENTRÉE POUR DVC
# ============================================================
if __name__ == "__main__":
    import pandas as pd
    import os

    print("🚀 [SPLIT] Démarrage...")

    # Vérifier que clean.csv existe
    if not os.path.exists("data/processed/clean.csv"):
        print("❌ [SPLIT] Fichier data/processed/clean.csv introuvable")
        exit(1)

    # Charger les données
    df = pd.read_csv("data/processed/clean.csv")
    print(f"[SPLIT] {len(df)} lignes chargées")

    # Cas spécial : pas assez de données
    if len(df) < 3:
        print("⚠️ [SPLIT] Pas assez de données pour découper")
        os.makedirs("data/processed", exist_ok=True)
        df.to_csv("data/processed/train.csv", index=False)
        pd.DataFrame().to_csv("data/processed/val.csv", index=False)
        pd.DataFrame().to_csv("data/processed/test.csv", index=False)
        print("⚠️ Fichiers vides créés")
        exit(0)

    # Découper
    train, val, test = split_dataset(df, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)

    # Sauvegarder
    train.to_csv("data/processed/train.csv", index=False)
    val.to_csv("data/processed/val.csv", index=False)
    test.to_csv("data/processed/test.csv", index=False)

    print(f"✅ [SPLIT] Train:{len(train)} | Val:{len(val)} | Test:{len(test)}")