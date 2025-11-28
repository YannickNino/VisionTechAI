from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from functools import wraps
import os
import sys
import csv
from datetime import datetime

# Import OCR logic and auth
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ocr_module import extract_garment_tag
from backend.auth import authenticate_user, validate_token, logout, add_user

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # Enable CORS for Vue.js frontend

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def token_required(f):
    """Decorator to require authentication token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token manquant'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        session = validate_token(token)
        if not session:
            return jsonify({'error': 'Token invalide ou expiré'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


@app.route('/')
def index():
    """Serve the Vue.js frontend"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/login')
def login_page():
    """Serve the login page"""
    return send_from_directory(app.static_folder, 'login.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'app': 'VisionTech OCR'})


@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Nom d\'utilisateur et mot de passe requis'}), 400
    
    auth_result = authenticate_user(username, password)
    
    if auth_result:
        return jsonify({
            'status': 'success',
            'token': auth_result['token'],
            'user': {
                'username': auth_result['username'],
                'name': auth_result['name']
            }
        })
    else:
        return jsonify({'error': 'Identifiants invalides'}), 401


@app.route('/api/logout', methods=['POST'])
@token_required
def logout_user():
    """User logout endpoint"""
    token = request.headers.get('Authorization')
    if token.startswith('Bearer '):
        token = token[7:]
    
    logout(token)
    return jsonify({'status': 'success', 'message': 'Déconnexion réussie'})


@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    
    if not username or not password or not name:
        return jsonify({'error': 'Tous les champs sont requis'}), 400
    
    if add_user(username, password, name):
        return jsonify({'status': 'success', 'message': 'Utilisateur créé avec succès'})
    else:
        return jsonify({'error': 'Nom d\'utilisateur déjà existant'}), 400


@app.route('/api/upload', methods=['POST'])
@token_required
def upload_images():
    """Upload multiple images and process them"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # Save uploaded files
    session_folder = os.path.join(UPLOAD_FOLDER, datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(session_folder, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(session_folder, filename)
            file.save(filepath)
            uploaded_files.append(filepath)
    
    if not uploaded_files:
        return jsonify({'error': 'No valid image files uploaded'}), 400
    
    # Process images
    results = []
    for filepath in sorted(uploaded_files):
        try:
            result = extract_garment_tag(filepath)
            if 'erreur' not in result:
                results.append({
                    'filename': os.path.basename(filepath),
                    'part': result['titre'],
                    'element': 'GARMENT TAG',
                    'valeur': result['garment_tag'],
                    'largeur': result.get('width', ''),
                    'longueur': result.get('height', '')
                })
            else:
                results.append({
                    'filename': os.path.basename(filepath),
                    'part': '',
                    'element': 'GARMENT TAG',
                    'valeur': 'Error',
                    'largeur': '',
                    'longueur': '',
                    'error': result['erreur']
                })
        except Exception as e:
            results.append({
                'filename': os.path.basename(filepath),
                'part': '',
                'element': 'GARMENT TAG',
                'valeur': 'Error',
                'largeur': '',
                'longueur': '',
                'error': str(e)
            })
    
    return jsonify({
        'status': 'success',
        'results': results,
        'session_folder': session_folder
    })


@app.route('/api/export-csv', methods=['POST'])
@token_required
def export_csv():
    """Export results to CSV"""
    data = request.json
    results = data.get('results', [])
    
    if not results:
        return jsonify({'error': 'No results to export'}), 400
    
    # Generate CSV file
    csv_filename = f"garment_tags_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = os.path.join(UPLOAD_FOLDER, csv_filename)
    
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Part', 'GARMENT TAG', 'largeur', 'longueur', 'fichier'])
            for result in results:
                writer.writerow([
                    result.get('part', ''),
                    result.get('valeur', ''),
                    result.get('largeur', ''),
                    result.get('longueur', ''),
                    result.get('filename', '')
                ])
        
        return send_file(csv_path, as_attachment=True, download_name=csv_filename)
    except Exception as e:
        return jsonify({'error': f'CSV export failed: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
