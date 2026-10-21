import sys
from PIL import Image, ImageDraw
def pair(a, b, box, out, labels=('before', 'after'), scale=1.0):
    A = Image.open(a).convert('RGB').crop(box); B = Image.open(b).convert('RGB').crop(box)
    if scale != 1.0:
        A = A.resize((int(A.width * scale), int(A.height * scale)), Image.LANCZOS); B = B.resize((int(B.width * scale), int(B.height * scale)), Image.LANCZOS)
    im = Image.new('RGB', (A.width + B.width + 8, A.height), (255, 255, 255)); im.paste(A, (0, 0)); im.paste(B, (A.width + 8, 0))
    d = ImageDraw.Draw(im); d.text((4, 2), labels[0], fill=(255, 255, 0)); d.text((A.width + 12, 2), labels[1], fill=(255, 255, 0))
    im.save(out, quality=88)
if __name__ == '__main__':
    a, b, x0, y0, x1, y1, out = sys.argv[1:8]
    s = float(sys.argv[8]) if len(sys.argv) > 8 else 1.0
    pair(a, b, (int(x0), int(y0), int(x1), int(y1)), out, scale=s)
