"""What this does: checks every word put on screen over pages 3 to 5 of chapter 2 for newcomers against what Malina
says (the estimated timeline's words): each on-screen line, the spoken word it comes in on and when, and whether every
word in it is one she says on that page (the signs + for "and", = for "as" or "means" and the arrow for "so" are
allowed). The on-screen lines are copied from page-3.js, page-4.js, page-5.js and works-effects.js (TAGS).
It also lists any digit on screen. Use: python3 -I words_check.py TIMELINE.json
"""
import json
import re
import sys

timeline = json.load(open(sys.argv[1]))
pages = {p['page']: p for p in timeline['pages']}
# (page, on-screen words, the spoken word it comes in on (and which time it is said on the page), the kind of thing)
ON_SCREEN = [
    (3, 'PICTURE TWO FACTORIES', ('Picture', 1), 'title, W3'),
    (3, 'EACH ONE = A WHOLE COUNTRY', ('country', 1), 'second line, W3'),
    (3, 'WORKERS', ('workers', 1), 'label to No. 1\'s queue, W3'),
    (3, 'MATERIALS', ('materials', 1), 'label to the crates at No. 2, W3'),
    (3, 'MACHINES', ('machines', 1), 'label to No. 2\'s lit sheds, W3'),
    (3, 'THE QUIET FACTORY', ('quiet', 1), 'title, W1'),
    (3, 'NEW MONEY SPENT', ('spends', 1), 'second line with an arrow into the gate, W1'),
    (3, 'MORE MONEY', ('More', 1), 'second line, W1'),
    (3, '+ MORE THINGS TO BUY', ('things', 1), 'second line, W1'),
    (3, '→ PRICES BARELY MOVE', ('barely', 1), 'second line, W1'),
    (3, 'PRICES', ('barely', 1), 'word on the level price arrow, W1'),
    (4, 'THE FLAT-OUT FACTORY', ('flat-out', 1), 'title, W2'),
    (4, 'FLAT OUT = WORKING AS HARD AS THEY CAN', ('flat-out', 1), 'second line, W2'),
    (4, 'NEW MONEY SPENT', ('spent', 1), 'third line, W2'),
    (4, 'WHAT HAPPENS TO PRICES?', ('prices', 1), 'question, W2'),
    (4, 'HAVE A GUESS', ('guess', 1), 'with the filling ring, W2'),
    (5, 'NO SPARE', ('spare', 1), 'title, W2'),
    (5, 'MORE MONEY', ('More', 1), 'second line, W2'),
    (5, '+ SAME THINGS TO BUY', ('same', 1), 'second line, W2'),
    (5, '→ PRICES UP', ('prices', 1), 'second line, W2'),
    (5, 'PRICES', ('prices', 1), 'word on the climbing price arrow, W2'),
    (5, 'QUIET', ('Most', 1), 'name tag on No. 1\'s chimney, W3 (the name from page 3)'),
    (5, 'FLAT OUT', ('Most', 1), 'name tag between No. 2\'s chimneys, W3 (the name from page 4)'),
    (5, 'MOST ECONOMISTS AGREE', ('agree', 1), 'small heading, W3'),
    (5, 'NEW MONEY SPENT', ('spent', 1), 'upper rule card, W3'),
    (5, '+ SPARE', ('spare', 2), 'upper rule card, W3'),
    (5, '→ MOSTLY MORE THINGS MADE', ('made', 2), 'upper rule card, W3'),
    (5, 'NOTHING SPARE', ('nothing', 1), 'lower rule card, W3'),
    (5, '→ MOSTLY PRICES UP', ('up', 2), 'lower rule card, W3'),
]
SIGNS = {'+': 'and', '=': 'as / means', '→': 'so', '?': ''}
# names carried from an earlier page: a tag may use the factory's name as given there
CARRIED = {5: [3, 4]}
# another form of a spoken word, allowed as a short form (on screen: said)
FORMS = {'spent': 'spends'}


def clean(word): return re.sub(r"[^a-z\-]", '', word.lower())


problems = 0
for page, text, (cue, nth), kind in ON_SCREEN:
    words = pages[page]['words']
    spoken = [clean(w['text']) for w in words]
    allowed = set(spoken)
    for earlier in CARRIED.get(page, []): allowed |= {clean(w['text']) for w in pages[earlier]['words']}
    allowed |= {part for word in list(allowed) for part in word.split('-')}   # "flat-out" said, FLAT OUT shown
    allowed |= {shown for shown, said_form in FORMS.items() if said_form in allowed}
    said = [w for w in words if clean(w['text']) == clean(cue)]
    at = said[nth - 1]['start'] if len(said) >= nth else None
    missing = [w for w in text.split() if w not in SIGNS and clean(w) not in allowed]
    digits = re.findall(r'\d', text)
    flag = 'ok' if not missing and not digits and at is not None else 'PROBLEM'
    if flag != 'ok': problems += 1
    extra = (f'; not said: {missing}' if missing else '') + (f'; digits: {digits}' if digits else '')
    print(f'page {page}  {text:40s} on "{cue}" ({at:.2f} s)  {kind}  {flag}{extra}')
for page in (3, 4, 5):
    print(f'\npage {page}, Malina: ' + ' '.join(w['text'] for w in pages[page]['words']))
print(f'\n{problems} problem(s)')
