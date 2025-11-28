# Système d'authentification VisionTech

## Vue d'ensemble
Système d'authentification simple avec nom d'utilisateur et mot de passe pour l'application VisionTech.

## Architecture

### Backend (Flask)
- **Fichier**: `backend/auth.py`
- **Stockage**: En mémoire (dictionnaire Python)
- **Sécurité**: Hash SHA256 pour les mots de passe
- **Sessions**: Tokens générés avec `secrets.token_urlsafe(32)`
- **Expiration**: 24 heures

### Frontend (Vue.js)
- **Page de connexion**: `frontend/login.html`
- **Application principale**: `frontend/index.html`
- **Stockage**: localStorage (token + informations utilisateur)

## Compte par défaut
```
Username: admin
Password: admin123
```

## API Endpoints

### POST /api/login
Authentification de l'utilisateur
```json
Request:
{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "token": "xxxxxxxxxxxxxxxx",
  "user": {
    "username": "admin",
    "name": "Administrateur"
  }
}
```

### POST /api/logout
Déconnexion de l'utilisateur
```json
Headers:
Authorization: Bearer <token>

Response:
{
  "success": true
}
```

### POST /api/register
Inscription d'un nouvel utilisateur
```json
Request:
{
  "username": "newuser",
  "password": "password123",
  "name": "Nouvel Utilisateur"
}

Response:
{
  "success": true,
  "user": {
    "username": "newuser",
    "name": "Nouvel Utilisateur"
  }
}
```

## Routes protégées
Les routes suivantes nécessitent un token valide dans le header `Authorization: Bearer <token>`:
- POST /api/upload
- POST /api/export-csv

## Flux d'authentification

### Connexion
1. L'utilisateur accède à `/login`
2. Saisit nom d'utilisateur et mot de passe
3. Le backend valide les identifiants et retourne un token
4. Le token et les infos utilisateur sont stockés dans localStorage
5. Redirection vers la page principale `/`

### Utilisation de l'application
1. À chaque chargement de page, vérification du token dans localStorage
2. Si pas de token → redirection vers `/login`
3. Le token est inclus dans toutes les requêtes API protégées
4. En cas d'erreur 401 → redirection vers `/login`

### Déconnexion
1. Clic sur le bouton "Déconnexion"
2. Appel à `/api/logout` pour invalider le token côté serveur
3. Suppression du token et des infos utilisateur de localStorage
4. Redirection vers `/login`

## Sécurité

### Implémentation actuelle
- ✅ Hash SHA256 des mots de passe
- ✅ Tokens aléatoires sécurisés (32 bytes)
- ✅ Expiration des sessions (24h)
- ✅ Validation du token à chaque requête
- ✅ Headers CORS configurés

### Limitations (pour un environnement de production)
- ⚠️ Stockage en mémoire (perte des données au redémarrage)
- ⚠️ Pas de salage des mots de passe (utiliser bcrypt)
- ⚠️ Pas de HTTPS forcé
- ⚠️ Pas de limite de tentatives de connexion
- ⚠️ Pas de token refresh automatique

## Démarrage

1. **Démarrer le serveur Flask**
```bash
cd backend
Flask run
```

2. **Accéder à l'application**
- Page de connexion: http://localhost:5000/login
- Application principale: http://localhost:5000/ (redirige vers /login si non authentifié)

3. **Se connecter**
- Utiliser le compte par défaut: admin / admin123
- Ou créer un nouveau compte via l'onglet "Inscription"

## Améliorations futures

Pour un déploiement en production, considérer:
1. Base de données persistante (SQLite, PostgreSQL)
2. Utilisation de bcrypt pour le hashage des mots de passe
3. Token refresh automatique
4. Rate limiting sur les tentatives de connexion
5. HTTPS obligatoire
6. Validation côté serveur plus stricte
7. Logs d'authentification
8. Récupération de mot de passe par email
9. Authentification à deux facteurs (2FA)
10. Gestion des rôles et permissions
