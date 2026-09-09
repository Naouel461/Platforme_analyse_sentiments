Cette plateforme analyse automatiquement les avis clients. Elle collecte les avis depuis Google Maps, détermine si chacun est positif, négatif ou neutre, puis affiche les résultats sous forme de graphiques et de tableaux de bord. Elle traite les avis en français et en arabe grâce à un modèle d'IA multilingue.



Ce guide s'adresse à trois profils. Les développeurs y trouveront les étapes pour installer et configurer la plateforme. Les administrateurs apprendront à gérer et maintenir le système. Les utilisateurs finaux découvriront comment se servir de l'interface web.



Une connaissance de base de la ligne de commande (Linux ou Windows PowerShell), de Docker et Docker Compose, et des concepts fondamentaux des API REST est nécessaire pour suivre ce guide.



Architecture de la plateforme



La plateforme repose sur six conteneurs Docker interconnectés.



Composant	Rôle	Technologie	Port exposé

Frontend	Interface utilisateur web	Nginx	3000

Backend (API)	Point d'entrée REST, logique métier	FastAPI	8002

Worker	Traitement asynchrone des avis	Python	-

PostgreSQL	Stockage persistant des prédictions	PostgreSQL 15	5432

Redis	Cache et file d'attente	Redis 7	6379

MinIO	Stockage objet (versionnement)	MinIO	9000/9001



Deux flux de données coexistent. Dans le flux synchrone, l'utilisateur saisit un mot-clé dans le frontend, qui envoie une requête à l'API. L'API appelle le scraper Playwright pour collecter les avis, chaque avis est analysé par le modèle BERT, les résultats sont sauvegardés en base de données puis retournés au frontend. Dans le flux asynchrone, une tâche est poussée dans Redis (sentiment\_tasks), le Worker la récupère, analyse le texte avec BERT, puis sauvegarde le résultat en base de données et dans Redis.



Prérequis



La configuration minimale demande 4 Go de RAM, 2 cœurs CPU, 20 Go de stockage et Windows 10/11, macOS ou Ubuntu 22.04. La configuration recommandée passe à 8 Go de RAM, 4 cœurs, 50 Go SSD et Ubuntu 22.04 LTS.



Les logiciels suivants sont nécessaires : Docker 20.10 ou plus récent, Docker Compose 2.0 ou plus récent (inclus avec Docker Desktop), Git 2.30 ou plus récent, PowerShell 5.1 ou plus récent sous Windows, et un navigateur récent (Chrome, Firefox, Edge).



Seuls les ports 3000 (frontend) et 8002 (API) sont indispensables. Les ports 5432 (PostgreSQL), 6379 (Redis), 9000 et 9001 (MinIO) ne sont nécessaires que pour un accès externe.



Installation et déploiement



Deux méthodes permettent de récupérer le projet. La première, recommandée, passe par Git :



git clone https://github.com/votre-repo/Platforme\_analyse\_sentiments.git

cd Platforme\_analyse\_sentiments





La seconde consiste à télécharger le projet depuis le dépôt, extraire le dossier, puis ouvrir un terminal dans le dossier extrait.



Le fichier .env contient toutes les configurations sensibles. Pour le créer :



\# Sur Linux/macOS

cp .env.example .env



\# Sur Windows (PowerShell)

Copy-Item .env.example .env





Avec Docker, les valeurs à renseigner sont les suivantes :



DB\_HOST=db          # Le nom du conteneur PostgreSQL

REDIS\_HOST=redis    # Le nom du conteneur Redis

MINIO\_ENDPOINT=minio:9000

API\_KEY=Cle\_naouel\_2026

DB\_PASSWORD=Pino2026   # À changer !





Sans Docker, pour le développement local uniquement, DB\_HOST et REDIS\_HOST doivent pointer vers localhost.



Pour vérifier la configuration sans afficher les mots de passe :



cat .env | grep -v PASSWORD





Le démarrage avec Docker Compose se fait en plusieurs étapes. D'abord, construire les images :



docker compose build





Cette commande lit les Dockerfiles et installe toutes les dépendances (Python, PyTorch, Playwright, etc.). Comptez 10 à 15 minutes la première fois. Ensuite, démarrer les services :



docker compose up -d





L'option -d fait tourner les conteneurs en arrière-plan. Vérifiez que tout fonctionne :



docker compose ps





Le résultat attendu liste six conteneurs avec leur statut. Les logs se consultent avec docker compose logs backend ou docker compose logs worker.



Un démarrage sans Docker est possible mais déconseillé en production. Il faut installer les dépendances Python, démarrer PostgreSQL, Redis et MinIO localement, puis lancer l'API et le Worker dans deux terminaux séparés.



Utilisation de la plateforme



Plusieurs interfaces sont accessibles :



Interface	URL	Description

Frontend	http://localhost:3000	Interface utilisateur principale

Dashboard	http://localhost:3000/dashboard.html	Tableau de bord temps réel

Admin	http://localhost:3000/admin.html	Interface administrateur

API Docs	http://localhost:8002/docs	Documentation Swagger

MinIO	http://localhost:9001	Console de stockage



Pour effectuer une recherche, ouvrez http://localhost:3000, saisissez un mot-clé (par exemple "Mytek Tunisie" ou "Boga Tunisie"), choisissez le nombre d'avis à analyser (5, 10, 15 ou 20) et cliquez sur "Analyser".



Les résultats s'affichent avec un code couleur : vert pour un avis positif, rouge pour un avis négatif, jaune pour un avis neutre. Un exemple d'affichage pourrait ressembler à ceci :



🔍 Résultats pour "Boga, Tunisie"



📊 10 avis trouvés



✅ Positifs : 8

❌ Négatifs : 2

⚪ Neutres : 0



⭐ Note moyenne : 4.5/5





Le dashboard, accessible sur http://localhost:3000/dashboard.html, se rafraîchit automatiquement toutes les 30 secondes. Il affiche les statistiques en temps réel (positifs, négatifs, neutres, total), des graphiques de répartition et de distribution, ainsi que l'historique des 50 dernières analyses.



L'interface admin, sur http://localhost:3000/admin.html, demande une authentification avec la clé API. Une fois connecté, vous pouvez charger les statistiques globales, consulter le taux de satisfaction, visualiser les prédictions des 7 derniers jours sur un graphique journalier, voir la répartition en camembert, et donner un feedback en cliquant sur "Utile" ou "Pas utile" pour améliorer le modèle.



Administration



La plateforme ne gère pas d'utilisateurs. L'accès admin est protégé par la clé API, dont la valeur par défaut est Cle\_naouel\_2026. Pour la changer, modifiez le fichier .env puis redémarrez le backend avec docker compose restart backend.



Pour interroger la base de données, plusieurs commandes utiles :



\# Voir les 10 dernières prédictions

docker exec ma\_base\_de\_donnees psql -U Naouel -d sentiment\_db -c "SELECT id, sentiment, LEFT(text, 50) as text FROM predictions ORDER BY id DESC LIMIT 10;"



\# Voir les statistiques par sentiment

docker exec ma\_base\_de\_donnees psql -U Naouel -d sentiment\_db -c "SELECT sentiment, COUNT(\*) FROM predictions GROUP BY sentiment;"



\# Compter les enregistrements

docker exec ma\_base\_de\_donnees psql -U Naouel -d sentiment\_db -c "SELECT COUNT(\*) FROM predictions;"





Pour nettoyer les données, supprimez les prédictions d'une source spécifique ou celles de moins de 3 caractères avec les commandes DELETE appropriées.



Le Worker se vérifie avec docker ps | grep worker, ses logs avec docker logs -f mon\_worker, et il se redémarre avec docker compose restart worker. Pour envoyer une tâche manuellement :



docker exec cache\_redis redis-cli LPUSH sentiment\_tasks '{"text":"Test manuel"}'





Redis se gère avec les commandes suivantes :



\# Voir les tâches en attente

docker exec cache\_redis redis-cli LLEN sentiment\_tasks



\# Voir les résultats en cache

docker exec cache\_redis redis-cli LRANGE sentiment\_results 0 -1



\# Vider le cache

docker exec cache\_redis redis-cli DEL sentiment\_results





La sauvegarde de PostgreSQL se fait avec pg\_dump, celle de MinIO avec mc mirror. La restauration utilise respectivement psql et mc mirror en sens inverse.



Maintenance



Pour mettre à jour la plateforme, arrêtez les services avec docker compose down, récupérez le nouveau code avec git pull, reconstruisez les images avec docker compose build, redémarrez avec docker compose up -d, puis vérifiez avec docker compose ps.



Les métriques Prometheus sont exposées sur http://localhost:8002/metrics. Elles incluent le nombre total de requêtes HTTP, le temps de réponse, l'utilisation CPU, l'utilisation mémoire et les fichiers ouverts.



Pour un contrôle rapide de l'état des services :



docker compose ps

docker compose logs --tail 50

curl http://localhost:8002/





Le nettoyage complet des conteneurs et volumes se fait avec docker compose down -v, suivi de docker image prune -a et docker volume prune pour supprimer les éléments inutilisés. Les fichiers temporaires se suppriment avec find sur Linux/macOS ou Get-ChildItem sous Windows PowerShell.



Résolution des problèmes



Quatre problèmes courants sont documentés. Si l'API ne répond pas (ERR\_CONNECTION\_REFUSED), vérifiez que le conteneur tourne, consultez les logs, redémarrez le backend et vérifiez le port avec netstat. Si le Worker ne consomme pas les tâches, vérifiez son état, ses logs, la file Redis, puis redémarrez-le. Si PostgreSQL ne démarre pas (statut unhealthy), consultez les logs, supprimez le volume en acceptant la perte de données, ou vérifiez les identifiants dans .env. Enfin, si Playwright renvoie une erreur "Executable doesn't exist", installez Chromium dans le conteneur ou reconstruisez l'image backend.



Un script de diagnostic complet est fourni. Il vérifie successivement les conteneurs Docker, l'accès à PostgreSQL, la réponse de Redis, l'état de l'API, du frontend, de MinIO et du Worker. Chaque test affiche un message clair de succès ou d'échec, ce qui permet d'identifier rapidement le composant défaillant.

