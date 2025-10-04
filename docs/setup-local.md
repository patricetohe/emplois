# Configuration locale pour l'agent LLM

## 1. Elasticsearch local (Docker)

### Démarrer Elasticsearch
```bash
# Démarrer les services
docker-compose up -d

# Vérifier que Elasticsearch fonctionne
curl http://localhost:9200/_cluster/health

# Interface Kibana (optionnel)
# http://localhost:5601
```

### Variables d'environnement pour l'agent
```bash
# Windows PowerShell
$env:ES_URL="http://localhost:9200"

# Linux/Mac
export ES_URL="http://localhost:9200"
```

## 2. Mistral API (externe)

### Obtenir une clé API
1. Aller sur https://console.mistral.ai/
2. Créer un compte et obtenir une clé API
3. Configurer les variables d'environnement

### Variables d'environnement
```bash
# Windows PowerShell
$env:MISTRAL_API_KEY="votre_cle_mistral" #f1gGUVdGHm4nbCTOz8N6Ck3o1daEV0E1

$env:MISTRAL_MODEL="mistral-small-latest"

# Linux/Mac
export MISTRAL_API_KEY="votre_cle_mistral"
export MISTRAL_MODEL="mistral-small-latest"
```

## 3. Installation des dépendances

```bash
# Dépendances IA
pip install -r ia-services/requirements.txt

# Redémarrer le serveur Django après installation
python backend/django_app/manage.py runserver
```

## 4. Test de l'agent

### Test avec FAISS seul (sans ES ni Mistral)
```bash
# POST http://localhost:8000/api/agent/ask/
{
  "query": "Je cherche un développeur Python à Lyon avec Django",
  "target": "candidates",
  "top_k": 5,
  "session_id": "demo-session-1"
}
```

### Test avec ES + FAISS (sans Mistral)
```bash
# Définir ES_URL puis redémarrer Django
$env:ES_URL="http://localhost:9200"

# Même requête POST
```

### Test complet (ES + FAISS + Mistral)
```bash
# Définir toutes les variables
$env:ES_URL="http://localhost:9200"
$env:MISTRAL_API_KEY="votre_cle"
$env:MISTRAL_MODEL="mistral-small-latest"

# 1. Dans le terminal PowerShell, tape exactement :
# $env:MISTRAL_API_KEY="f1gGUVdGHm4nbCTOz8N6Ck3o1daEV0E1"
# $env:MISTRAL_MODEL="mistral-small-latest"
# $env:ES_URL="http://localhost:9200"
# 2. Vérifier que c'est bien défini :

# echo $env:MISTRAL_API_KEY
# echo $env:MISTRAL_MODEL
# echo $env:ES_URL
# Tu devrais voir :
# f1gGUVdGHm4nbCTOz8N6Ck3o1daEV0E1
# mistral-small-latest
# http://localhost:9200

# Redémarrer Django et tester
```

## 5. Indexation des données

### Vérifier les stats FAISS
```bash
# GET http://localhost:8000/api/matching/stats/
```

### Indexer un candidat
```bash
# POST http://localhost:8000/api/matching/index-candidate/
{
  "candidate_id": 17
}
```

### Indexer une offre
```bash
# POST http://localhost:8000/api/matching/index-job-offer/
{
  "job_offer_id": 123
}
```

## 6. Arrêt des services

```bash
# Arrêter Docker
docker-compose down

# Supprimer les volumes (optionnel)
docker-compose down -v
```
