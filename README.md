# VisionTech - OCR GARMENT TAG Extractor

Application web moderne pour l'extraction automatique des valeurs GARMENT TAG depuis des images.

## 🚀 Technologies

- **Backend**: Flask (Python)
- **Frontend**: Vue.js 3
- **OCR**: Tesseract + pytesseract
- **Design**: CSS moderne avec gradients

## 📋 Prérequis

- Python 3.8+
- Tesseract OCR installé (`C:\Program Files\Tesseract-OCR\tesseract.exe`)
- Navigateur web moderne

## 🛠️ Installation

### 1. Installer les dépendances Python

```bash
cd backend
pip install -r requirements.txt
```

### 2. Lancer le serveur Flask

```bash
Flask run
```

Le serveur démarre sur `http://localhost:5000`

### 3. Ouvrir l'interface web

Ouvrez `frontend/index.html` dans votre navigateur, ou servez-le avec:

```bash
cd frontend
python -m http.server 8080
```

Puis accédez à `http://localhost:8080`

## 🎯 Utilisation

1. **Upload d'images**
   - Cliquez ou glissez-déposez vos images
   - Formats supportés: PNG, JPG, JPEG, BMP, TIFF

2. **Traitement**
   - Cliquez sur "Traiter les images"
   - L'OCR analyse chaque image et extrait les données

3. **Résultats**
   - Visualisez les résultats dans un tableau
   - Colonnes: Part, Element, Valeur, Largeur, Longueur

4. **Export CSV**
   - Cliquez sur "Exporter CSV" pour télécharger les résultats

## 📁 Structure du projet

```
Projet1/
├── backend/
│   ├── app_flask.py        # Serveur Flask
│   ├── requirements.txt    # Dépendances Python
│   └── uploads/            # Dossier temporaire
├── frontend/
│   └── index.html          # Interface Vue.js
├── ocr_module.py           # Logique OCR
└── app.py                  # Script CLI (version originale)
```

## 🔧 API Endpoints

- `GET /api/health` - Health check
- `POST /api/upload` - Upload et traitement des images
- `POST /api/export-csv` - Export CSV des résultats

## 🎨 Fonctionnalités

- ✅ Upload multiple d'images (drag & drop)
- ✅ Traitement OCR automatique avec recadrage intelligent
- ✅ Affichage des résultats en temps réel
- ✅ Export CSV des données
- ✅ Interface moderne et responsive
- ✅ Gestion des erreurs
- ✅ Extraction de: Part, Valeur GARMENT TAG, Dimensions

## 📝 Notes

- Les images sont temporairement stockées dans `backend/uploads/`
- Le recadrage automatique améliore la précision OCR
- Les patterns regex capturent différents formats (10 X GARMENT TAG, 7X*GARMENT TAG, etc.)

## 🐛 Dépannage

**Problème**: Tesseract non trouvé
- Vérifiez l'installation de Tesseract
- Adaptez le chemin dans `ocr_module.py` ligne 11

**Problème**: CORS error
- Vérifiez que Flask-CORS est installé
- Le serveur Flask doit tourner sur port 5000

**Problème**: Images non traitées
- Vérifiez les formats d'image supportés
- Consultez les logs Flask pour les erreurs OCR

## 📄 Licence

Projet VisionTech - 2025
