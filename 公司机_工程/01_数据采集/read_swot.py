import sys
# Remove venv from path to avoid PIL conflict
sys.path = [p for p in sys.path if 'hermes-agent' not in p]

import pytesseract
from PIL import Image

img_path = r'C:\Users\Administrator\AppData\Roaming\Hermes\composer-images\composer_2026-07-03_03-11-13-396_112468.png'
img = Image.open(img_path)
print(f"Image size: {img.size}")
print(f"Image mode: {img.mode}")

# Try OCR
text = pytesseract.image_to_string(img, lang='chi_sim+eng')
print("\n=== OCR TEXT ===")
print(text)
