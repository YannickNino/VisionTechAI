# Guide de démarrage rapide - VisionTech avec authentification

## 📋 Prérequis
- Python 3.12.6
- Tesseract-OCR installé à: C:\Program Files\Tesseract-OCR\tesseract.exe
- Environnement virtuel (.venv) avec les packages installés

## 🚀 Démarrage

### 1. Activer l'environnement virtuel
```powershell
.venv\Scripts\Activate.ps1
```

### 2. Démarrer le serveur Flask
```powershell
cd backend
python app_flask.py
```

Le serveur démarre sur http://localhost:5000

### 3. Accéder à l'application
Ouvrir dans un navigateur:
- **Page de connexion**: http://localhost:5000/login
- **Application**: http://localhost:5000/ (redirige vers /login si non connecté)

## 🔐 Connexion

### Compte par défaut
```
Nom d'utilisateur: admin
Mot de passe: admin123
```

### Créer un nouveau compte
1. Cliquer sur l'onglet "Inscription" sur la page de connexion
2. Remplir le formulaire (nom complet, nom d'utilisateur, mot de passe)
3. Cliquer sur "S'inscrire"
4. Se connecter avec les nouveaux identifiants

## 📸 Utilisation

### Traiter des images
1. Se connecter à l'application
2. Cliquer sur la zone de téléchargement ou glisser-déposer des images
3. Formats acceptés: PNG, JPG, JPEG, BMP, TIFF
4. Cliquer sur "Traiter les images"
5. Les résultats s'affichent dans un tableau

### Exporter en CSV
1. Après le traitement des images
2. Cliquer sur "Exporter CSV"
3. Le fichier `garment_tags_results.csv` sera téléchargé

### Se déconnecter
Cliquer sur le bouton "Déconnexion" en haut à droite

## 🔧 Résolution de problèmes

### Erreur "Token manquant" ou "Token invalide"
- La session a expiré (24h)
- Se reconnecter via http://localhost:5000/login

### Erreur lors du traitement d'images
- Vérifier que Tesseract-OCR est installé
- Vérifier le chemin dans `ocr_module.py`

### Page blanche ou erreur 404
- Vérifier que le serveur Flask est démarré
- Vérifier l'URL: http://localhost:5000/login

### Les résultats ne s'affichent pas
- Ouvrir la console du navigateur (F12)
- Vérifier les erreurs réseau ou CORS
- Vérifier que le token est valide

## 📁 Structure des fichiers

```
Projet1/
├── backend/
│   ├── app_flask.py       # Serveur Flask avec API
│   ├── auth.py            # Module d'authentification
│   ├── requirements.txt   # Dépendances Python
│   └── uploads/           # Images téléchargées
├── frontend/
│   ├── index.html         # Application principale (Vue.js)
│   └── login.html         # Page de connexion (Vue.js)
├── ocr_module.py          # Logique OCR Tesseract
├── app.py                 # Script CLI (ancienne version)
├── README.md              # Documentation principale
└── AUTHENTICATION.md      # Documentation authentification
```

## 🎨 Interface utilisateur

### Couleurs
- Fond: Bleu foncé (#0c1e3d → #1a3a6b)
- Boutons principaux: Bleu (#2563eb → #1e40af)
- Boutons secondaires: Rouge (#dc2626 → #b91c1c)

### Fonctionnalités
- ✅ Drag & drop d'images
- ✅ Sélection multiple de fichiers
- ✅ Affichage des résultats en tableau
- ✅ Export CSV
- ✅ Authentification sécurisée
- ✅ Déconnexion
- ✅ Inscription de nouveaux utilisateurs

## 📊 Extraction de données

L'application extrait automatiquement:
- **Part**: Code de la pièce (ex: P01, P02)
- **Element**: "GARMENT TAG"
- **Valeur**: Nombre avant "GARMENT TAG" (ex: 10, 7)
- **Largeur**: Largeur de l'image 
- **Longueur**: Hauteur de l'image 
- **Fichier**: Nom du fichier source

## 🔒 Sécurité

### Implémentée
- Hash SHA256 des mots de passe
- Tokens sécurisés (32 bytes)
- Expiration des sessions (24h)
- Validation du token à chaque requête
- Protection des routes API

### Pour la production
Voir AUTHENTICATION.md pour les améliorations recommandées
