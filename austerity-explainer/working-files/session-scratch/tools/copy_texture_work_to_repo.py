# What this does: copies a tidy snapshot of the procedural-texture work from the scratch folder into the repository: all guides, code,
# reports, scores and descriptions, plus only the pictures the guides point to, shrunk and re-saved
# without hidden metadata. It leaves out the user's own reference pictures, downloaded programs, and the big baked maps (they can be
# re-made from the recipes). Private machine paths inside text files are replaced with short neutral names.
# Use: python3 -I copy_texture_work_to_repo.py SOURCE_FOLDER DESTINATION_FOLDER
import os, re, shutil, sys
from PIL import Image

source, destination = sys.argv[1], sys.argv[2]
TEXT = {'.md', '.py', '.json', '.sh', '.txt', '.tsv', '.csv'}
SCRATCH = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
SESSION_FILES = '/root/.claude/projects/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921'
REPLACEMENTS = [(SCRATCH + '/proc-work', 'proc-work'), (SCRATCH, 'scratchpad'), (SESSION_FILES, 'session-files'),
                ('02fc5154-76f5-5aac-a505-860164e7e921', 'SESSION')]


def skip_folder(relative):
    parts = relative.split(os.sep)
    if '__pycache__' in parts or (parts and parts[0] == 'reference'):
        return True
    if parts and parts[0] == 'third-party' and len(parts) >= 3 and parts[2] not in ('notes', 'tools', 'scripts', 'analysis'):
        return True
    return False


def wanted_text(relative, size):
    if os.path.splitext(relative)[1].lower() not in TEXT:
        return False
    if size > 1_200_000:
        return False
    return True


# pictures the markdown files point to
referenced = set()
for root, dirs, files in os.walk(source):
    for name in files:
        if name.endswith('.md'):
            path = os.path.join(root, name)
            text = open(path, errors='ignore').read()
            for link in re.findall(r'\]\(([^)\s]+\.(?:png|jpg))\)', text) + re.findall(r'`([^`\s]+\.(?:png|jpg))`', text):
                link = link.replace('%20', ' ')
                for candidate in (os.path.normpath(os.path.join(root, link)), os.path.normpath(os.path.join(source, link))):
                    if os.path.exists(candidate):
                        referenced.add(os.path.abspath(candidate))

copied_text = copied_pictures = 0
picture_bytes = text_bytes = 0
for root, dirs, files in os.walk(source):
    relative_root = os.path.relpath(root, source)
    if relative_root != '.' and skip_folder(relative_root):
        dirs[:] = []
        continue
    for name in files:
        path = os.path.join(root, name)
        relative = os.path.normpath(os.path.join(relative_root, name))
        size = os.path.getsize(path)
        target = os.path.join(destination, relative)
        extension = os.path.splitext(name)[1].lower()
        if wanted_text(relative, size):
            os.makedirs(os.path.dirname(target), exist_ok=True)
            text = open(path, errors='ignore').read()
            for old, new in REPLACEMENTS:
                text = text.replace(old, new)
            open(target, 'w').write(text)
            copied_text += 1
            text_bytes += len(text.encode())
        elif extension in ('.png', '.jpg') and (os.path.abspath(path) in referenced or name.startswith('06 Overview')):
            image = Image.open(path)
            image.load()
            if image.mode not in ('RGB', 'L', 'RGBA'):
                image = image.convert('RGB')
            if size > 150_000 and max(image.size) > 1200:
                scale = 1200 / max(image.size)
                image = image.resize((int(image.size[0] * scale), int(image.size[1] * scale)), Image.LANCZOS)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            if extension == '.jpg':
                image.save(target, quality=85, optimize=True)
            elif size > 150_000:
                image.quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(target, optimize=True)
            else:
                image.save(target, optimize=True)
            copied_pictures += 1
            picture_bytes += os.path.getsize(target)
print(f'text files {copied_text} ({text_bytes / 1e6:.1f} MB), pictures {copied_pictures} ({picture_bytes / 1e6:.1f} MB)')
