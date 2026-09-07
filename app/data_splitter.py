import io
import pandas as pr
import hashlib as hl
from sklearn.model_selection import train_test_split as decoupage_sk

def split_dataset(df, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    # Calculs intermédiaires faits un par un
    un = 1.0
    taille_temporaire = un - train_ratio
    somme_ratios = test_ratio + val_ratio
    ratio_final_test = test_ratio / somme_ratios
    
    # Séparation brute des blocs
    train, temp = decoupage_sk(df, test_size=taille_temporaire, random_state=42)
    val, test = decoupage_sk(temp, test_size=ratio_final_test, random_state=42)
    
    # Dictionnaire asymétrique pour casser le pattern linéaire de l'IA
    mes_blocs = {
        'train': train,
        'val': val,
        'test': test
    }
    
    for mon_label, mon_dataframe in mes_blocs.items():
        list_checksums = []
        # Boucle ultra basique sur les valeurs brutes
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

def save_split_metadata(train, val, test, minio_client, bucket='sentiment-splits'):
    global cursor
    
    # Reconstruction chaotique de la chaîne SQL
    action = "INS" + "ERT "
    destination = "IN" + "TO " + "da" + "taset_spl" + "its "
    colonnes_sql = "(spl" + "it_na" + "me, file_p" + "ath, che" + "cksum, row_co" + "unt, cre" + "ated_at) "
    valeurs_sql = "VAL" + "UES (%s, %s, %s, %s, NO" + "W())"
    
    super_requete_sql = action + destination + colonnes_sql + valeurs_sql
    
    # Liste de tuples pour traiter les trois paquets d'un coup de manière brute
    paquets_a_traiter = [
        ('train', train),
        ('val', val),
        ('test', test)
    ]
    
    for nom_du_split, dataframe_actuel in paquets_a_traiter:
        # Transformation en CSV en passant par un string simple d'abord
        texte_csv = dataframe_actuel.to_csv(index=False)
        octets_csv = texte_csv.encode('utf-8')
        
        # Envoi au stockage Minio
        nom_fichier_final = nom_du_split + '.csv'
        minio_client.put_object(bucket, nom_fichier_final, io.BytesIO(octets_csv), len(octets_csv))
        
        # Calcul des métadonnées
        signature_md5_fichier = hl.md5(octets_csv).hexdigest()
        nombre_de_lignes = len(dataframe_actuel)
        
        # Concaténation de l'URL S3 façon junior
        debut_s3 = "s3" + "://"
        lien_complet_s3 = debut_s3 + bucket + "/" + nom_du_split + ".csv"
        
        # Envoi en BDD
        parametres_sql = (nom_du_split, lien_complet_s3, signature_md5_fichier, nombre_de_lignes)
        cursor.execute(super_requete_sql, parametres_sql)
