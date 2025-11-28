"""
OCR Module for VisionTech
Extracts GARMENT TAG values from images
"""

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import os

# Configure Tesseract path
os.environ['PATH'] = 'C:\\Program Files\\Tesseract-OCR;' + os.environ.get('PATH', '')
pytesseract.pytesseract.pytesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


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
    """Locate GARMENT TAG in image and crop around it."""
    search_variants = [
        ('original', image, 1.0),
        ('grayscale', image.convert('L'), 1.0),
    ]
    
    try:
        pre = preprocess_image(image)
        search_variants.append(('preprocessed', pre, 2.0))
    except Exception:
        pass
    
    garment_boxes = []
    
    for variant_name, variant_img, scale_factor in search_variants:
        try:
            data = pytesseract.image_to_data(variant_img, output_type=pytesseract.Output.DICT, lang='eng')
            
            for i, word in enumerate(data['text']):
                if word and ('GARMENT' in word.upper() or 'TAG' in word.upper()):
                    conf = int(data['conf'][i])
                    if conf > 30:
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                        x_orig = int(x / scale_factor)
                        y_orig = int(y / scale_factor)
                        w_orig = int(w / scale_factor)
                        h_orig = int(h / scale_factor)
                        garment_boxes.append((x_orig, y_orig, w_orig, h_orig, conf, variant_name))
        except Exception:
            pass
    
    if not garment_boxes:
        return image, False
    
    best_box = max(garment_boxes, key=lambda b: b[4])
    x, y, w, h, conf, variant = best_box
    
    img_width, img_height = image.size
    
    expand_left = max(0, x - w * 3)
    expand_right = min(img_width, x + w * 5)
    expand_top = max(0, y - h * 2)
    expand_bottom = min(img_height, y + h * 3)
    
    cropped = image.crop((expand_left, expand_top, expand_right, expand_bottom))
    
    return cropped, True


def extract_garment_tag(image_path):
    """Extract the GARMENT TAG value from an image."""
    try:
        filename = os.path.basename(image_path)
        title = os.path.splitext(filename)[0]
        p = re.search(r'(P\d+)', title, re.IGNORECASE)
        if p:
            title = p.group(1)

        img = Image.open(image_path)
        
        cropped_img, found_tag = find_and_crop_garment_tag_region(img)
        
        if found_tag:
            working_img = cropped_img
            working_size = cropped_img.size
        else:
            working_img = img
            working_size = img.size

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
        for vname, vimg in variants:
            for cfg in configs:
                try:
                    txt = pytesseract.image_to_string(vimg, lang='eng', config=cfg)
                except Exception:
                    txt = ''
                if txt and txt.strip():
                    ocr_results.append((vname, cfg, txt))

        patterns_before = [
            r'([0-9]+)\s+X\s+GARMENT\s+TAG',
            r'([0-9]+)\s*X\s*GARMENT',
            r'([0-9]+)\s*\*\s*GARMENT\s+TAG',
            r'([0-9A-Z]+)\s*\*\s*GARMENT',
            r'([0-9]+)\s+GARMENT\s+TAG',
            r'([A-Z0-9\-]+)\s*GARMENT\s+TAG',
            r'([^\s]+)\s*\*\s*GARMENT',
            r'([A-Z0-9]+)[^A-Z0-9]*GARMENT',
        ]
        
        patterns_after = [
            r'GARMENT\s+TAG[:\s]*([0-9]+)',
            r'TAG[:\s]*([0-9]+)',
            r'GARMENT\s+TAG[:\s]+([0-9A-Z\-]+)',
            r'TAG[:\s]+([0-9A-Z\-]+)',
        ]

        candidates = []
        for vname, cfg, txt in ocr_results:
            norm = re.sub(r'\s+', ' ', txt)
            
            for pat in patterns_before:
                matches = re.finditer(pat, norm, re.IGNORECASE)
                for m in matches:
                    val = re.sub(r'[^A-Za-z0-9\-]', '', m.group(1).strip())
                    val = re.sub(r'X+$', '', val, flags=re.IGNORECASE)
                    if val and len(val) <= 10:
                        candidates.append((val, 'before', vname, cfg))
            
            for pat in patterns_after:
                matches = re.finditer(pat, norm, re.IGNORECASE)
                for m in matches:
                    val = re.sub(r'[^A-Za-z0-9\-]', '', m.group(1).strip())
                    val = re.sub(r'X+$', '', val, flags=re.IGNORECASE)
                    if val and len(val) <= 10:
                        candidates.append((val, 'after', vname, cfg))

        if candidates:
            before_candidates = [c for c in candidates if c[1] == 'before']
            after_candidates = [c for c in candidates if c[1] == 'after']
            
            numeric_before = [(v, pos, vname, cfg) for v, pos, vname, cfg in before_candidates if v.isdigit()]
            numeric_after = [(v, pos, vname, cfg) for v, pos, vname, cfg in after_candidates if v.isdigit()]
            
            if numeric_before:
                counts = {}
                for val, *_ in numeric_before:
                    counts[val] = counts.get(val, 0) + 1
                best = sorted(counts.items(), key=lambda x: (-x[1], -len(x[0]), -int(x[0]) if x[0].isdigit() else 0))[0][0]
                return {'titre': title, 'garment_tag': best, 'candidates': candidates, 'used_cropping': found_tag, 'width': working_size[0], 'height': working_size[1]}
            elif numeric_after:
                counts = {}
                for val, *_ in numeric_after:
                    counts[val] = counts.get(val, 0) + 1
                best = sorted(counts.items(), key=lambda x: (-x[1], -len(x[0]), -int(x[0]) if x[0].isdigit() else 0))[0][0]
                return {'titre': title, 'garment_tag': best, 'candidates': candidates, 'used_cropping': found_tag, 'width': working_size[0], 'height': working_size[1]}
            elif before_candidates:
                counts = {}
                for val, *_ in before_candidates:
                    counts[val] = counts.get(val, 0) + 1
                best = sorted(counts.items(), key=lambda x: (-x[1], -sum(ch.isdigit() for ch in x[0]), len(x[0])))[0][0]
                return {'titre': title, 'garment_tag': best, 'candidates': candidates, 'used_cropping': found_tag, 'width': working_size[0], 'height': working_size[1]}
            else:
                counts = {}
                for val, *_ in after_candidates:
                    counts[val] = counts.get(val, 0) + 1
                best = sorted(counts.items(), key=lambda x: (-x[1], -sum(ch.isdigit() for ch in x[0]), len(x[0])))[0][0]
                return {'titre': title, 'garment_tag': best, 'candidates': candidates, 'used_cropping': found_tag, 'width': working_size[0], 'height': working_size[1]}
        else:
            samples = [t[:200] for _, _, t in ocr_results[:3]]
            return {'titre': title, 'garment_tag': 'Not found', 'candidates': candidates, 'sample_texts': samples, 'used_cropping': found_tag, 'width': working_size[0], 'height': working_size[1]}

    except FileNotFoundError:
        return {'erreur': f"L'image n'a pas été trouvée: {image_path}"}
    except Exception as e:
        import traceback
        return {'erreur': f"Une erreur s'est produite: {str(e)}", 'traceback': traceback.format_exc()}
