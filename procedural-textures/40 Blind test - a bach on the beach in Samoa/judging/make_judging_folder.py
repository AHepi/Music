"""
What this file does:
Makes the folder three fresh judges score from, blind: the two final pictures under shuffled letters, the look's
reference pictures, the look page and the question sheet. The letter-to-builder key is written OUTSIDE the folder
the judges see, in key.json next to this script.

    python3 make_judging_folder.py --plugin PICTURE --control PICTURE --out FOLDER
"""

import argparse
import json
import random
import shutil
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
PLUGIN = Path('/home/claude/music/plugins/painted-place')

QUESTIONS = """# Judge these pictures

You are judging two pictures of the same request, made by two different builders. You do not know who made which, and you do not need to. Look at every picture in `reference/` first (they show a series' look), then at `pictures/A.jpg` and `pictures/B.jpg` at full size.

The request both builders were given, in the owner's words: "A bach on the beach in Samoa. Modern day." (A bach is a small, simple holiday house by the sea.)

Score each picture from 0 to 10 on each of these three questions, then answer the two questions below. Scores are whole numbers. Be as hard on one as on the other.

1. **Photograph:** could this be a photograph of a real place? (10 = you would believe it; 0 = a toy or a diagram)
2. **Request:** does it deliver the request - a bach, on a beach, in Samoa, today? (10 = all four, unmistakably)
3. **Film backdrop in the look:** could it stand as a backdrop in a film with the look of the reference pictures - the light, the colour, the air, the framing, the finish? (10 = it belongs with them)

Then:
- Which picture would you choose for the film, and why, in three sentences?
- For each picture, the first thing you would fix, in one sentence a non-technical person could act on.

Answer in this form and nothing else:

| Picture | Photograph | Request | Film backdrop in the look |
|---|---|---|---|
| A | n | n | n |
| B | n | n | n |

Choice: A or B, then three sentences.
Fix A: one sentence.
Fix B: one sentence.
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plugin', required=True)
    parser.add_argument('--control', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()
    out = Path(args.out)
    (out / 'pictures').mkdir(parents=True, exist_ok=True)
    (out / 'reference').mkdir(exist_ok=True)
    rng = random.Random(args.seed)
    order = ['plugin', 'control']
    rng.shuffle(order)
    sources = {'plugin': args.plugin, 'control': args.control}
    key = {}
    for letter, who in zip('AB', order):
        picture = Image.open(sources[who]).convert('RGB')
        picture.save(out / 'pictures' / f'{letter}.jpg', quality=92)
        key[letter] = who
    for reference in sorted((PLUGIN / 'look' / 'reference').glob('*.jpg')):
        shutil.copy(reference, out / 'reference' / reference.name)
    shutil.copy(PLUGIN / 'look' / 'The look.md', out / 'The look.md')
    (out / 'Judge these pictures.md').write_text(QUESTIONS)
    (HERE / 'key.json').write_text(json.dumps({'folder': str(out), 'letters': key, 'sources': sources}, indent=2))
    print('judging folder:', out)
    print('key (not in the folder):', key)


if __name__ == '__main__':
    main()
