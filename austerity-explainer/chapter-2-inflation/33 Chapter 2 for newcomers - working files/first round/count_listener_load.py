# What this does: counts the "listener load" in chapter 2 as recorded. Each item below is one thing a
# first-time listener has to take in (a new place, a year or date, a number, or a term a newcomer may
# not know), tagged by hand with the moment Malina says it (seconds from the start of the chapter, read
# from chapter-2-inflation/narration/timeline.json). It prints the load per page and per 30 seconds,
# and the speaking speed per page measured from the recording.
# Run: python3 -I count_listener_load.py /path/to/timeline.json

import json
import sys

# kind: P = place (a change of place), Y = year or date, N = number, T = term or reference a newcomer may lack
LOAD_ITEMS = [
    # page 1
    (1, 2.4, 'T', 'creating new money (chapter 1 idea, not explained)'),
    (1, 4.0, 'T', 'inflation (explained six seconds later)'),
    (1, 18.5, 'T', 'the shell factory (chapter 1 reference)'),
    # page 2
    (2, 20.9, 'P', 'Britain'),
    (2, 21.8, 'Y', '1915'),
    (2, 23.4, 'T', 'unemployment (explained: "the share of workers without a job")'),
    (2, 26.4, 'N', 'under one percent'),
    (2, 29.7, 'T', 'paid for partly with new money (by whom? chapter 1)'),
    (2, 30.7, 'T', 'submarines sinking supply ships (whose?)'),
    (2, 33.6, 'T', 'turned over to war work (idiom)'),
    (2, 35.5, 'T', 'more money chasing fewer things (idiom)'),
    (2, 38.6, 'Y', 'the end of the war (1918, not said)'),
    (2, 40.5, 'N', 'roughly doubled'),
    # page 3
    (3, 43.6, 'P', 'two imagined factories'),
    (3, 47.5, 'T', 'idle'),
    (3, 53.0, 'T', 'shells (sea shells? artillery?)'),
    (3, 59.9, 'T', 'flat out (idiom)'),
    (3, 65.1, 'T', 'bid against each other'),
    (3, 68.0, 'P', 'back to Britain at war'),
    # page 4
    (4, 74.9, 'T', '"Homes work the same way" (as what?)'),
    (4, 76.9, 'Y', '1915'),
    (4, 79.3, 'P', 'Glasgow'),
    (4, 83.4, 'N', 'as much as a quarter'),
    (4, 84.4, 'Y', 'November'),
    (4, 85.9, 'N', 'twenty thousand'),
    (4, 87.4, 'T', 'refusing to pay the rise (rent strike; "rise" as a noun)'),
    (4, 90.3, 'T', 'Parliament (which one?)'),
    (4, 90.9, 'T', 'froze rents (metaphor)'),
    # page 5
    (5, 95.9, 'T', '"So test it" (test what? the rule was never said)'),
    (5, 96.8, 'P', 'Japan'),
    (5, 97.6, 'Y', '2013'),
    (5, 99.3, 'T', 'central bank (explained)'),
    (5, 101.2, 'T', 'yen'),
    (5, 102.6, 'N', 'double'),
    (5, 104.5, 'N', 'in two years'),
    (5, 108.5, 'T', "they'd soar (if-then, rare verb)"),
    (5, 109.6, 'N', 'eight years'),
    (5, 111.9, 'N', 'about half a percent a year'),
    (5, 114.0, 'Y', '2008'),
    (5, 114.7, 'T', 'the 2008 crash (not explained)'),
    (5, 115.4, 'P', 'Britain again (Bank of England)'),
    (5, 118.0, 'N', 'hundreds of billions of pounds'),
    (5, 123.2, 'T', 'shares'),
    (5, 123.8, 'T', 'other investments'),
    (5, 125.1, 'T', 'the gains ... whoever owned the most (the most what?)'),
    # page 6
    (6, 128.7, 'P', 'Germany'),
    (6, 129.5, 'Y', '1923'),
    (6, 132.5, 'T', 'prices are already racing (idiom)'),
    (6, 133.9, 'P', 'French and Belgian soldiers'),
    (6, 136.1, 'P', 'the Ruhr'),
    (6, 138.1, 'T', 'heartland'),
    (6, 140.6, 'T', 'stop work in protest (against what?)'),
    (6, 144.6, 'Y', 'November'),
    (6, 147.4, 'N', 'more than four trillion'),
    (6, 148.4, 'T', 'German marks; a dollar "costing" marks (exchange rate)'),
    # page 7
    (7, 156.2, 'Y', 'late 1973'),
    (7, 156.4, 'P', 'no place named (whose prices?)'),
    (7, 161.0, 'N', 'nearly quadruples'),
    (7, 162.4, 'N', 'about three months'),
    (7, 166.6, 'T', 'dearer'),
    (7, 169.3, 'T', '"spending" (a new name for new money)'),
    (7, 170.4, 'T', 'costs'),
    (7, 171.3, 'P', '"here" = New Zealand'),
    (7, 172.4, 'Y', 'the latest figures (2026, not said)'),
    (7, 174.0, 'N', 'four point one percent'),
    (7, 175.3, 'T', 'in the year to June'),
    (7, 176.6, 'T', 'leave fuel out'),
    (7, 178.1, 'N', 'two point nine'),
    # page 8
    (8, 181.0, 'T', '"So yes" (yes to what?)'),
    (8, 190.5, 'Y', '2021'),
    (8, 191.8, 'P', 'New Zealand ("our")'),
    (8, 193.9, 'T', 'since records began'),
    (8, 196.5, 'N', 'about thirty percent'),
    (8, 197.4, 'N', 'twelve months'),
    (8, 198.8, 'T', 'independent review'),
    (8, 200.0, 'T', 'Reserve Bank (explained only on page 10)'),
    (8, 201.2, 'T', '"the support" (what support? the pandemic is never mentioned)'),
    (8, 205.3, 'T', 'too strong, for too long'),
    # page 9
    (9, 209.7, 'T', 'the usual cure'),
    (9, 211.1, 'P', 'Britain again'),
    (9, 211.8, 'Y', '1920'),
    (9, 214.6, 'T', 'interest rate (explained: "the price of borrowing")'),
    (9, 217.3, 'N', 'seven percent'),
    (9, 224.0, 'N', 'about two percent'),
    (9, 225.0, 'N', 'eleven percent'),
    (9, 228.4, 'T', 'pay with their jobs (idiom)'),
    (9, 229.8, 'T', 'Mattei (never introduced in chapter 2)'),
    (9, 231.2, 'T', '"that was part of the point" (what was?)'),
    (9, 233.2, 'T', 'fewer jobs to go round (idiom)'),
    (9, 235.7, 'T', 'the power to ask for more (more what?)'),
    # page 10
    (10, 238.8, 'P', '"Here" = New Zealand'),
    (10, 240.8, 'T', 'Reserve Bank (now explained)'),
    (10, 243.4, 'N', 'a quarter of a percent'),
    (10, 244.7, 'N', 'five and a half percent'),
    (10, 246.1, 'Y', '2023'),
    (10, 249.4, 'Y', 'the end of 2021'),
    (10, 252.4, 'N', 'three point two percent'),
    (10, 253.8, 'N', 'five point six'),
    (10, 255.8, 'Y', 'this year'),
    (10, 263.8, 'T', '"Spent on what?" (the rule in three words)'),
]

KINDS = ['P', 'Y', 'N', 'T']
KIND_NAMES = {'P': 'places', 'Y': 'years/dates', 'N': 'numbers', 'T': 'terms/references'}


def main(timeline_path):
    timeline = json.load(open(timeline_path))
    pages = timeline['pages']

    print('PER PAGE (speaking time = first word to last word)')
    print(f"{'page':>4} {'words':>5} {'secs':>5} {'wpm':>4}  " + '  '.join(f'{k:>2}' for k in KINDS) + '  all  items/10s')
    total_words = 0
    total_speaking = 0.0
    for page in pages:
        words = page['words']
        start, end = words[0]['start'], words[-1]['end']
        seconds = end - start
        total_words += len(words)
        total_speaking += seconds
        counts = {k: sum(1 for item in LOAD_ITEMS if item[0] == page['page'] and item[2] == k) for k in KINDS}
        all_items = sum(counts.values())
        print(f"{page['page']:>4} {len(words):>5} {seconds:>5.1f} {len(words) / seconds * 60:>4.0f}  "
              + '  '.join(f'{counts[k]:>2}' for k in KINDS) + f'  {all_items:>3}  {all_items / seconds * 10:>5.1f}')
    print(f'total words {total_words}, speaking time {total_speaking:.1f} s, '
          f'average {total_words / total_speaking * 60:.0f} words a minute (plan: 140)')
    print(f'at 140 words a minute the same speaking time holds {total_speaking / 60 * 140:.0f} words')

    print()
    print('PER 30 SECONDS OF FILM')
    print(f"{'window':>9}  " + '  '.join(f'{k:>2}' for k in KINDS) + '  all')
    for window_start in range(0, 270, 30):
        window_items = [item for item in LOAD_ITEMS if window_start <= item[1] < window_start + 30]
        counts = {k: sum(1 for item in window_items if item[2] == k) for k in KINDS}
        label = f'{window_start // 60}:{window_start % 60:02d}-{(window_start + 30) // 60}:{(window_start + 30) % 60:02d}'
        print(f'{label:>9}  ' + '  '.join(f'{counts[k]:>2}' for k in KINDS) + f'  {sum(counts.values()):>3}')

    print()
    print('TOTALS: ' + ', '.join(f'{KIND_NAMES[k]} {sum(1 for item in LOAD_ITEMS if item[2] == k)}' for k in KINDS))


if __name__ == '__main__':
    main(sys.argv[1])
