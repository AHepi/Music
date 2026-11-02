"""
What this file does:
Makes one folder per judge for the second blind test, so each fresh judge scores the two final pictures blind: the
pictures under letters shuffled separately for each judge (so neither builder always comes first), the look's reference
pictures, the look page and the question sheet. The letter-to-builder key is written OUTSIDE the folders, in key.json
next to this script.

    python3 make_judging_folders.py --plugin PICTURE --control PICTURE --out FOLDER --judges 4
"""

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
LOOK = Path('/home/claude/blind-test-2/control-build/target')

QUESTIONS = """# Judge these pictures

You are judging two pictures of the same request, made by two different builders. You do not know who made which, and you do not need to. Look at every picture in `reference/` first (they show a film's look, and `The look.md` describes it), then at `pictures/A.jpg` and `pictures/B.jpg` at full size.

The request both builders were given, in the owner's words: "A tea house."

Score each picture from 0 to 10 on each of these four questions, then answer the two questions below. Scores are whole numbers. Be as hard on one as on the other.

1. **Photograph:** could this be a photograph of a real place? (10 = you would believe it; 0 = a toy or a diagram)
2. **Request:** does it deliver the request - a tea house, unmistakably? (10 = anyone would say "a tea house" at once)
3. **Film backdrop in the look:** could it stand as a backdrop in a film with the look of the reference pictures - the light, the colour, the air, the framing, the finish? (10 = it belongs with them)
4. **Old and used:** do the surfaces look old, used and lived-in - wet, grimy, mossy, weedy, weathered, with small things gathered where things collect? (10 = as old and used as the references; 0 = clean and new)

Then:
- Which picture would you choose for the film, and why, in three sentences?
- For each picture, the first thing you would fix, in one sentence a non-technical person could act on.

Answer in this form and nothing else:

| Picture | Photograph | Request | Film backdrop in the look | Old and used |
|---|---|---|---|---|
| A | n | n | n | n |
| B | n | n | n | n |

Choice: A or B, then three sentences.
Fix A: one sentence.
Fix B: one sentence.
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plugin', required=True)
    parser.add_argument('--control', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--judges', type=int, default=4)
    args = parser.parse_args()
    sources = {'plugin': args.plugin, 'control': args.control}
    pictures = {who: Image.open(path).convert('RGB') for who, path in sources.items()}
    key = {'sources': sources, 'judges': {}}
    for number in range(1, args.judges + 1):
        folder = Path(args.out) / f'judge {number}'
        (folder / 'pictures').mkdir(parents=True, exist_ok=True)
        (folder / 'reference').mkdir(exist_ok=True)
        order = ['plugin', 'control'] if number % 2 else ['control', 'plugin']    # half the judges see each builder first
        letters = {}
        for letter, who in zip('AB', order):
            pictures[who].save(folder / 'pictures' / f'{letter}.jpg', quality=92)
            letters[letter] = who
        for reference in sorted((LOOK / 'reference').glob('*.jpg')):
            shutil.copy(reference, folder / 'reference' / reference.name)
        shutil.copy(LOOK / 'The look.md', folder / 'The look.md')
        (folder / 'Judge these pictures.md').write_text(QUESTIONS)
        key['judges'][str(folder)] = letters
    (HERE / 'key.json').write_text(json.dumps(key, indent=2))
    print('folders made under', args.out)


if __name__ == '__main__':
    main()
