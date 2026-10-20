# What this does: reads markdown guides and checks that every relative link and picture link in them points to a file that exists.
# Links may be written plainly, with %20 for spaces, or inside <angle brackets>. Web links (http...) and links inside `code` are skipped.
# Usage: python3 -I check_links.py GUIDE.md [GUIDE.md ...]      prints each broken link and a count; exit code 1 if any link is broken.
import re
import sys
import urllib.parse
import os

LINK_PATTERN = re.compile(r'!?\[[^\]]*\]\((<[^>]+>|[^)\s]+)(?:\s+"[^"]*")?\)')


def links_in(markdown_text):
    without_code = re.sub(r'`[^`]*`', '', markdown_text)
    for match in LINK_PATTERN.finditer(without_code):
        target = match.group(1)
        if target.startswith('<') and target.endswith('>'):
            target = target[1:-1]
        yield target


def main(guide_paths):
    broken_count, checked_count = 0, 0
    for guide_path in guide_paths:
        folder = os.path.dirname(os.path.abspath(guide_path))
        with open(guide_path, encoding='utf-8') as handle:
            text = handle.read()
        for target in links_in(text):
            if re.match(r'^[a-z]+://', target) or target.startswith('#') or target.startswith('mailto:'):
                continue
            file_part = urllib.parse.unquote(target.split('#')[0])
            if not file_part:
                continue
            checked_count += 1
            if not os.path.exists(os.path.join(folder, file_part)):
                broken_count += 1
                print('BROKEN in %s: %s' % (os.path.basename(guide_path), target))
    print('checked %d links in %d files, %d broken' % (checked_count, len(guide_paths), broken_count))
    return 1 if broken_count else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
