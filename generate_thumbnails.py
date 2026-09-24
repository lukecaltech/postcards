import os
import sys
import subprocess

try:
    from PIL import Image
except ImportError:
    print("Pillow not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

IMAGE_DIR = "images"
THUMB_DIR = r"c:\Users\lukec\Pictures\Postcards\letter\website\thumbnails"
TOTAL_POSTCARDS = 37
THUMB_SIZE = (600, 600)

os.makedirs(THUMB_DIR, exist_ok=True)

print(f"Generating thumbnails in {THUMB_DIR}...")
for i in range(1, TOTAL_POSTCARDS + 1):
    num_str = f"{i:03d}"
    front_img = os.path.join(IMAGE_DIR, f"postcard{num_str}.jpg")
    thumb_img = os.path.join(THUMB_DIR, f"thumb_{num_str}.jpg")
    
    if os.path.exists(front_img):
        # Skip if thumbnail already exists
        if not os.path.exists(thumb_img):
            try:
                with Image.open(front_img) as img:
                    # Convert to RGB if needed
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
                    img.save(thumb_img, "JPEG", quality=80)
                print(f"Created thumbnail for postcard {num_str}")
            except Exception as e:
                print(f"Error processing {front_img}: {e}")
    else:
        print(f"Warning: Could not find {front_img}")

print("Thumbnail generation complete!")
