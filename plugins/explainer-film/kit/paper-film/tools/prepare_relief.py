"""What this does: gets a painting ready to be a room with depth on the cinema stage. It copies the
painting (as a high-quality JPEG) and turns its depth map (from fal's Depth Anything: light = near,
dark = far) into a smaller, gently smoothed grey picture, so the 3D surface made from it has no
jagged steps. Both land in the relief folder as NAME.jpg and NAME-depth.png.

Use: python3 -I prepare_relief.py PAINTING DEPTH_MAP RELIEF_FOLDER [NAME] [--blur PIXELS]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter


def main():
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    blur = 2.0
    if "--blur" in sys.argv:
        blur = float(sys.argv[sys.argv.index("--blur") + 1])
        arguments = [a for a in arguments if a != sys.argv[sys.argv.index("--blur") + 1]]
    painting_path, depth_path, folder = arguments[:3]
    name = arguments[3] if len(arguments) > 3 else os.path.splitext(os.path.basename(painting_path))[0]
    os.makedirs(folder, exist_ok=True)
    painting = Image.open(painting_path).convert("RGB")
    painting.save(os.path.join(folder, f"{name}.jpg"), quality=93)
    depth = Image.open(depth_path).convert("L")
    small = depth.resize((512, round(512 * depth.height / depth.width)), Image.LANCZOS)
    small = small.filter(ImageFilter.GaussianBlur(blur))
    values = np.asarray(small).astype(np.float32)
    low, high = np.percentile(values, 0.5), np.percentile(values, 99.5)
    values = np.clip((values - low) / max(1.0, high - low), 0, 1) * 255
    Image.fromarray(values.astype(np.uint8)).save(os.path.join(folder, f"{name}-depth.png"))
    print(f"{name}: painting {painting.size}, depth {small.size}")


if __name__ == "__main__":
    main()
