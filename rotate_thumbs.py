import os
from PIL import Image

THUMB_DIR = r"c:\Users\lukec\Pictures\Postcards\letter\website\thumbnails"

# List of postcard IDs to rotate 180 degrees
to_rotate = [2, 3, 4, 6, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24]

print("Rotating specific thumbnails 180 degrees...")
for i in to_rotate:
    num_str = f"{i:03d}"
    thumb_path = os.path.join(THUMB_DIR, f"thumb_{num_str}.jpg")
    
    if os.path.exists(thumb_path):
        try:
            with Image.open(thumb_path) as img:
                # Rotate 180 degrees
                rotated = img.rotate(180)
                rotated.save(thumb_path, "JPEG", quality=85)
            print(f"Successfully rotated thumb_{num_str}.jpg")
        except Exception as e:
            print(f"Error rotating {thumb_path}: {e}")
    else:
        print(f"Warning: Could not find {thumb_path}")

print("Rotation complete!")
