import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import os
from tkinter import Tk, filedialog
import sys
import csv

# Configure Tesseract path
os.environ['PATH'] = 'C:\\Program Files\\Tesseract-OCR;' + os.environ.get('PATH', '')
pytesseract.pytesseract.pytesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


def select_folder():
    """Open a dialog to select a folder containing images.

    Tries Tkinter folder dialog first; if that fails or returns empty,
    falls back to console input so the script can run in non-GUI
    or headless situations.
    """
    try:
        print('Opening folder selection dialog...')
        root = Tk(); root.withdraw()
        path = filedialog.askdirectory(title='Sélectionnez le dossier contenant les images')
        root.destroy()
        if path:
            print(f'Selected folder: {path}')
            return path
        else:
            print('No folder selected from dialog.')
    except Exception as e:
        print(f'Warning: folder dialog failed: {e}')

    # Fallback to console input
    try:
        fallback = input('Enter folder path (or press Enter to cancel): ').strip()
    except Exception:
        fallback = ''
    if fallback:
        print(f'Using path from input: {fallback}')
        return fallback
    return None


def select_image_file():
    """Open a dialog to select a single image file, with console fallback."""
    try:
        print('Opening file selection dialog...')
        root = Tk(); root.withdraw()
        path = filedialog.askopenfilename(title='Sélectionnez une image', filetypes=[('Images','*.png *.jpg *.jpeg *.bmp *.tiff *.tif'),('All Files','*.*')])
        root.destroy()
        if path:
            print(f'Selected: {path}')
            return path
        else:
            print('No file selected from dialog.')
    except Exception as e:
        print(f'Warning: file dialog failed: {e}')

    # Fallback to console input
    try:
        fallback = input('Enter image path (or press Enter to cancel): ').strip()
    except Exception:
        fallback = ''
    if fallback:
        print(f'Using path from input: {fallback}')
        return fallback
    return None


def preprocess_image(image):
    """Simple PIL-based preprocessing to improve OCR."""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    w, h = image.size
    image = image.resize((w*2, h*2), Image.Resampling.LANCZOS)
    gray = image.convert('L')
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    gray = ImageEnhance.Brightness(gray).enhance(1.05)
    gray = ImageEnhance.Sharpness(gray).enhance(1.8)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    thresh = 128
    data = [255 if p > thresh else 0 for p in gray.getdata()]
    out = Image.new('L', gray.size)
    out.putdata(data)
    return out


def find_and_crop_garment_tag_region(image):
    """Locate GARMENT TAG in image and crop around it.
    
    Returns a tuple: (cropped_image, found_garment_tag)
    If GARMENT TAG is not found, returns (original_image, False)
    """
    # print('\n=== Searching for GARMENT TAG in image ===')
    
    # Try multiple preprocessing variants to locate the text
    search_variants = [
        ('original', image, 1.0),
        ('grayscale', image.convert('L'), 1.0),
    ]
    
    # Try to add preprocessed variant (scaled 2x)
    try:
        pre = preprocess_image(image)
        search_variants.append(('preprocessed', pre, 2.0))
    except Exception:
        pass
    
    garment_boxes = []
    
    for variant_name, variant_img, scale_factor in search_variants:
        try:
            # Get OCR data with bounding boxes
            data = pytesseract.image_to_data(variant_img, output_type=pytesseract.Output.DICT, lang='eng')
            
            # Look for "GARMENT" or "TAG" words
            for i, word in enumerate(data['text']):
                if word and ('GARMENT' in word.upper() or 'TAG' in word.upper()):
                    conf = int(data['conf'][i])
                    if conf > 30:  # Minimum confidence
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                        # Adjust coordinates back to original image scale
                        x_orig = int(x / scale_factor)
                        y_orig = int(y / scale_factor)
                        w_orig = int(w / scale_factor)
                        h_orig = int(h / scale_factor)
                        garment_boxes.append((x_orig, y_orig, w_orig, h_orig, conf, variant_name))
                        # print(f'Found "{word}" at ({x_orig},{y_orig}) size={w_orig}x{h_orig} conf={conf} in {variant_name}')
        except Exception as e:
            pass  # print(f'Warning: OCR detection failed for {variant_name}: {e}')
    
    if not garment_boxes:
        # print('GARMENT TAG not found in image - using full image')
        return image, False
    
    # Use the detection with highest confidence
    best_box = max(garment_boxes, key=lambda b: b[4])
    x, y, w, h, conf, variant = best_box
    # print(f'Using best detection: ({x},{y}) size={w}x{h} conf={conf} from {variant}')
    
    # Expand crop region to capture text before and after GARMENT TAG
    img_width, img_height = image.size
    
    # Expand: left by 300%, right by 200%, top/bottom by 150%
    expand_left = max(0, x - w * 3)
    expand_right = min(img_width, x + w * 5)
    expand_top = max(0, y - h * 2)
    expand_bottom = min(img_height, y + h * 3)
    
    # print(f'Cropping region: left={expand_left}, top={expand_top}, right={expand_right}, bottom={expand_bottom}')
    cropped = image.crop((expand_left, expand_top, expand_right, expand_bottom))
    
    return cropped, True


def extract_garment_tag(image_path):
    """Extract the GARMENT TAG value from an image using cropping and multiple OCR attempts."""
    try:
        filename = os.path.basename(image_path)
        title = os.path.splitext(filename)[0]
        p = re.search(r'(P\d+)', title, re.IGNORECASE)
        if p:
            title = p.group(1)

        img = Image.open(image_path)
        # Silent mode: comment out for debugging
        # print(f'\nProcessing image: {filename}')
        # print(f'Image size: {img.size}')
        
        # Try to find and crop around GARMENT TAG
        cropped_img, found_tag = find_and_crop_garment_tag_region(img)
        
        if found_tag:
            # print('\n=== Using CROPPED region for OCR ===')
            working_img = cropped_img
            working_size = cropped_img.size
        else:
            # print('\n=== Using FULL image for OCR ===')
            working_img = img
            working_size = img.size

        # prepare variants from cropped/full image
        variants = [('orig', working_img)]
        try:
            pre = preprocess_image(working_img)
        except Exception:
            pre = working_img
        variants.append(('pre', pre))
        variants.append(('pre_contrast', ImageEnhance.Contrast(pre).enhance(2.2)))
        variants.append(('pre_sharp', ImageEnhance.Sharpness(pre).enhance(2.0)))

        configs = ['', '--oem 1 --psm 6', '--oem 3 --psm 11', '--oem 3 --psm 7']
        ocr_results = []
        # print(f'\nRunning OCR with {len(variants)} variants and {len(configs)} configs...')
        for vname, vimg in variants:
            for cfg in configs:
                try:
                    txt = pytesseract.image_to_string(vimg, lang='eng', config=cfg)
                except Exception:
                    txt = ''
                if txt and txt.strip():
                    ocr_results.append((vname, cfg, txt))
                    # Debug: print first few OCR results (disabled for batch mode)
                    # if len(ocr_results) <= 3:
                    #     print(f'  OCR sample [{vname}, {cfg or "default"}]: {txt.strip()[:100]}')

        # Enhanced patterns focused on text BEFORE GARMENT TAG
        patterns_before = [
            r'([0-9]+)\s+X\s+GARMENT\s+TAG',     # "10 X GARMENT TAG"
            r'([0-9]+)\s*X\s*GARMENT',           # "10X GARMENT" or "10 X GARMENT"
            r'([0-9]+)\s*\*\s*GARMENT\s+TAG',    # "2*GARMENT TAG"
            r'([0-9A-Z]+)\s*\*\s*GARMENT',        # "2*GARMENT"
            r'([0-9]+)\s+GARMENT\s+TAG',          # "2 GARMENT TAG"
            r'([A-Z0-9\-]+)\s*GARMENT\s+TAG',     # Any alphanumeric before GARMENT TAG
            r'([^\s]+)\s*\*\s*GARMENT',           # anything*GARMENT
            r'([A-Z0-9]+)[^A-Z0-9]*GARMENT',      # alphanumeric directly before GARMENT
        ]
        
        # Patterns after GARMENT TAG (higher priority now for values like "10")
        patterns_after = [
            r'GARMENT\s+TAG[:\s]*([0-9]+)',      # "GARMENT TAG 10" or "GARMENT TAG:10"
            r'TAG[:\s]*([0-9]+)',                 # "TAG 10" or "TAG:10"
            r'GARMENT\s+TAG[:\s]+([0-9A-Z\-]+)', # "GARMENT TAG 10" alphanumeric
            r'TAG[:\s]+([0-9A-Z\-]+)',           # "TAG 10" alphanumeric
        ]

        candidates = []
        # print('\n=== Analyzing OCR results ===')
        for vname, cfg, txt in ocr_results:
            norm = re.sub(r'\s+', ' ', txt)
            
            # Prioritize "before" patterns
            for pat in patterns_before:
                matches = re.finditer(pat, norm, re.IGNORECASE)
                for m in matches:
                    val = re.sub(r'[^A-Za-z0-9\-]', '', m.group(1).strip())
                    # Remove trailing X and keep only digits
                    val = re.sub(r'X+$', '', val, flags=re.IGNORECASE)
                    if val and len(val) <= 10:  # Sanity check
                        candidates.append((val, 'before', vname, cfg))
                        pass  # print(f'  Found (before): "{val}" in {vname} with {cfg or "default"}')
            
            # Check "after" patterns with lower priority
            for pat in patterns_after:
                matches = re.finditer(pat, norm, re.IGNORECASE)
                for m in matches:
                    val = re.sub(r'[^A-Za-z0-9\-]', '', m.group(1).strip())
                    # Remove trailing X and keep only digits
                    val = re.sub(r'X+$', '', val, flags=re.IGNORECASE)
                    if val and len(val) <= 10:
                        candidates.append((val, 'after', vname, cfg))
                        pass  # print(f'  Found (after): "{val}" in {vname} with {cfg or "default"}')

        # pick best candidate (prioritize numeric values)
        if candidates:
            # Separate before and after candidates
            before_candidates = [c for c in candidates if c[1] == 'before']
            after_candidates = [c for c in candidates if c[1] == 'after']
            
            # Filter to keep only numeric or mostly numeric candidates
            numeric_before = [(v, pos, vname, cfg) for v, pos, vname, cfg in before_candidates if v.isdigit()]
            numeric_after = [(v, pos, vname, cfg) for v, pos, vname, cfg in after_candidates if v.isdigit()]
            
            # Prioritize numeric candidates (favor longer values like "10" over "1")
            if numeric_before:
                counts = {}
                for val, *_ in numeric_before:
                    counts[val] = counts.get(val, 0) + 1
                # Sort by: count (higher better), then length (longer better), then value (higher better)
                best = sorted(counts.items(), key=lambda x: (-x[1], -len(x[0]), -int(x[0]) if x[0].isdigit() else 0))[0][0]
                # print(f'\n✓ Best candidate (before, numeric): {best}')
                return {'titre': title, 'garment_tag': best, 'candidates': candidates, 'used_cropping': found_tag, 'width': working_size[0], 'height': working_size[1]}
            elif numeric_after:
                counts = {}
                for val, *_ in numeric_after:
                    counts[val] = counts.get(val, 0) + 1
                # Sort by: count (higher better), then length (longer better), then value (higher better)
                best = sorted(counts.items(), key=lambda x: (-x[1], -len(x[0]), -int(x[0]) if x[0].isdigit() else 0))[0][0]
                # print(f'\n✓ Best candidate (after, numeric): {best}')
                return {'titre': title, 'garment_tag': best, 'candidates': candidates, 'used_cropping': found_tag, 'width': working_size[0], 'height': working_size[1]}
            # Fallback to any before/after candidates
            elif before_candidates:
                counts = {}
                for val, *_ in before_candidates:
                    counts[val] = counts.get(val, 0) + 1
                best = sorted(counts.items(), key=lambda x: (-x[1], -sum(ch.isdigit() for ch in x[0]), len(x[0])))[0][0]
                # print(f'\n✓ Best candidate (before): {best}')
                return {'titre': title, 'garment_tag': best, 'candidates': candidates, 'used_cropping': found_tag, 'width': working_size[0], 'height': working_size[1]}
            else:
                counts = {}
                for val, *_ in after_candidates:
                    counts[val] = counts.get(val, 0) + 1
                best = sorted(counts.items(), key=lambda x: (-x[1], -sum(ch.isdigit() for ch in x[0]), len(x[0])))[0][0]
                # print(f'\n✓ Best candidate (after): {best}')
                return {'titre': title, 'garment_tag': best, 'candidates': candidates, 'used_cropping': found_tag, 'width': working_size[0], 'height': working_size[1]}
        else:
            samples = [t[:200] for _, _, t in ocr_results[:3]]
            # print('\n✗ No candidates found')
            # print('Sample OCR texts:')
            # for s in samples:
            #     print(f'  {s}')
            return {'titre': title, 'garment_tag': 'Not found', 'candidates': candidates, 'sample_texts': samples, 'used_cropping': found_tag, 'width': working_size[0], 'height': working_size[1]}

    except FileNotFoundError:
        return {'erreur': f"L'image n'a pas été trouvée: {image_path}"}
    except Exception as e:
        import traceback
        return {'erreur': f"Une erreur s'est produite: {str(e)}", 'traceback': traceback.format_exc()}


if __name__ == '__main__':
    print('=== OCR GARMENT TAG Extractor - Batch Mode ===')
    print('Sélectionnez le dossier contenant les images\n')
    
    folder_path = select_folder()
    
    if not folder_path:
        print('\n❌ Aucun dossier sélectionné. Programme terminé.')
        sys.exit(1)
    
    if not os.path.exists(folder_path):
        print(f'\n❌ Erreur: Le dossier n\'existe pas: {folder_path}')
        sys.exit(1)
    
    # Find all image files in the folder
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')
    image_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith(image_extensions):
            image_files.append(os.path.join(folder_path, file))
    
    if not image_files:
        print(f'\n❌ Aucune image trouvée dans le dossier: {folder_path}')
        sys.exit(1)
    
    # Sort images by filename (to get P01, P02, P03... in order)
    image_files.sort()
    
    print(f'\n📁 Dossier: {folder_path}')
    print(f'📸 Nombre d\'images trouvées: {len(image_files)}\n')
    print('Traitement en cours...\n')
    
    # Process all images
    results = []
    for image_path in image_files:
        result = extract_garment_tag(image_path)
        if 'erreur' not in result:
            results.append(result)
        else:
            filename = os.path.basename(image_path)
            print(f'⚠️  Erreur pour {filename}: {result["erreur"]}\n')
    
    # Display results in table format
    print('\n' + '=' * 80)
    print(f'{"Part":<10} {"Element":<15} {"valeur":<10} {"largeur":<10} {"longueur":<10}')
    print('-' * 80)
    for result in results:
        largeur = result.get('width', '')
        longueur = result.get('height', '')
        print(f'{result["titre"]:<10} {"GARMENT TAG":<15} {result["garment_tag"]:<10} {largeur:<10} {longueur:<10}')
    print('=' * 80)
    print(f'\n✅ {len(results)} images traitées avec succès!')
    
    # Ask if user wants to export to CSV
    export_choice = input('\nExporter les résultats en CSV? (o/n): ').strip().lower()
    
    if export_choice == 'o' or export_choice == 'oui':
        csv_filename = os.path.join(folder_path, 'garment_tags_results.csv')
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Part', 'Element', 'valeur', 'largeur', 'longueur'])
                for result in results:
                    writer.writerow([
                        result['titre'],
                        'GARMENT TAG',
                        result['garment_tag'],
                        result.get('width', ''),
                        result.get('height', '')
                    ])
            print(f'\n📄 Résultats exportés vers: {os.path.abspath(csv_filename)}')
            print(f'✅ Fichier créé avec succès!')
            
            # Verify file exists
            if os.path.exists(csv_filename):
                file_size = os.path.getsize(csv_filename)
                print(f'   Taille: {file_size} octets')
            else:
                print('⚠️  Attention: Le fichier n\'a pas été trouvé après création!')
        except Exception as e:
            print(f'\n⚠️  Erreur lors de l\'export CSV: {e}')
            import traceback
            print(traceback.format_exc())
    else:
        print('\nExport CSV annulé.')
