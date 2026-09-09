Write-Host "?? Démarrage de la plateforme d'analyse de sentiments..." -ForegroundColor Cyan

# 1. Démarrer Docker Compose
Write-Host "?? Démarrage des conteneurs Docker..." -ForegroundColor Yellow
docker-compose up -d

# 2. Attendre que les services soient prêts
Write-Host "? Attente du démarrage des services..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 3. Vérifier l'état
Write-Host "`n?? État des services:" -ForegroundColor Cyan
docker-compose ps

# 4. Ouvrir les URLs
Write-Host "`n?? URLs disponibles:" -ForegroundColor Cyan
Write-Host "   API Backend: http://localhost:8002" -ForegroundColor Green
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "   Minio Console: http://localhost:9001" -ForegroundColor Green
Write-Host "   PostgreSQL: localhost:5432" -ForegroundColor Green
Write-Host "   Redis: localhost:6379" -ForegroundColor Green

# 5. Démarrer le worker
Write-Host "`n?? Démarrage du Worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\venvs\pyscaffold_env\Platforme_analyse_sentiments'; Write-Host 'Worker - Analyse de sentiments' -ForegroundColor Cyan; `$env:REDIS_HOST='localhost'; `$env:DB_HOST='localhost'; python worker.py"

Write-Host "`n? Tous les services sont démarrés !" -ForegroundColor Green
Write-Host "?? Pour arrêter, exécutez: docker-compose down" -ForegroundColor Yellow
