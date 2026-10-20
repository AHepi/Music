# What this does: checks that a "description" file (the compact list of numbers a recipe is driven by, found by analysing a reference
# picture) really is a description and not a picture in disguise. It reports the file size, how many numbers it holds, the biggest
# list, and refuses (exit code 1) if it finds anything that looks like per-dot picture data: a list of more than 4000 numbers,
# nested lists that form a grid of more than 64 x 64, text that looks like an embedded image, or a file larger than the size limit.
# Elements (a brick: position, size, colour), curves (control points), colour palettes and noise settings are fine. Pixels are not.
# Use:  python3 -I description_audit.py DESCRIPTION.json [--limit-kilobytes 64]
import json
import sys


def audit(data, limit_bytes, raw_text):
    problems = []
    counts = {'numbers': 0, 'biggest_list': 0, 'biggest_list_path': ''}

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f'{path}/{key}')
        elif isinstance(node, list):
            if len(node) > counts['biggest_list']:
                counts['biggest_list'], counts['biggest_list_path'] = len(node), path
            flat = 0
            for item in node:
                if isinstance(item, (int, float)):
                    flat += 1
            if flat > 4000:
                problems.append(f'{path}: a flat list of {flat} numbers (more than 4000: looks like picture data)')
            if len(node) > 64 and all(isinstance(row, list) and len(row) > 64 and all(isinstance(v, (int, float)) for v in row[:5]) for row in node[:5]):
                problems.append(f'{path}: a grid of {len(node)} x {len(node[0])} numbers (looks like an image)')
            for index, item in enumerate(node):
                walk(item, f'{path}[{index}]')
        elif isinstance(node, (int, float)):
            counts['numbers'] += 1
        elif isinstance(node, str) and len(node) > 2000:
            problems.append(f'{path}: a text of {len(node)} characters (looks like an embedded file)')

    walk(data, '')
    if len(raw_text.encode()) > limit_bytes:
        problems.append(f'file is {len(raw_text.encode())} bytes, over the limit of {limit_bytes}')
    return problems, counts


def main():
    path = sys.argv[1]
    limit = 1024 * float(sys.argv[sys.argv.index('--limit-kilobytes') + 1]) if '--limit-kilobytes' in sys.argv else 64 * 1024
    raw = open(path).read()
    data = json.loads(raw)
    problems, counts = audit(data, limit, raw)
    size = len(raw.encode())
    print(json.dumps({'file': path, 'bytes': size, 'numbers': counts['numbers'], 'biggest_list': counts['biggest_list'],
                      'biggest_list_at': counts['biggest_list_path'], 'share_of_a_1254x1254_rgb_picture': round(size / (1254 * 1254 * 3), 4),
                      'problems': problems}, indent=1))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
