"""What this does: makes an ESTIMATED chapter timeline (the same form as assemble_chapter_narration.py's
timeline.json) from a narration script alone, before anything is recorded, so page files can be built and
checked on the narrator's words. Each word's length and each pause are measured from a real recording of the
same narrator (a word-times file): how long a word lasts for its number of letters, and how long she pauses
after a full stop, a comma, a question mark and a "...". When the real recording exists, the real timeline
replaces this one and the pages retime themselves (they ask for words, not seconds).

Use: python3 -I estimate_timeline.py NARRATION_SCRIPT.json MEASURED_WORD_TIMES.json OUT_TIMELINE.json
        [--pause-after PAGE=SECONDS ...] [--default-pause 1.5] [--slower 1.0]
  --pause-after 4=4.0  a longer gap after page 4 (for a held guess); --slower 1.1 stretches every word and
  pause by 10% (to see the length if the voice were slowed).
"""
import argparse
import json
import re
import statistics

FIRST_WORD_AT = 1.08     # as assemble_chapter_narration.py
TAIL_AFTER_LAST_WORD = 4.0
FRAMES_PER_SECOND = 30


def letters(word):
    return len(re.sub(r'[^A-Za-z0-9]', '', word))


def ending(word):
    if word.endswith('...') or word.endswith('…'):
        return 'pause'
    if word.endswith('?'):
        return 'question'
    if word.endswith('.') or word.endswith('!'):
        return 'stop'
    if word.endswith(',') or word.endswith(';') or word.endswith(':'):
        return 'comma'
    return 'none'


def measure(word_times):
    """How long a plain word lasts for its letters (a straight line through words with no punctuation), how much
    longer a word lasts when it ends a sentence, a clause or a "..." (the transcript puts the pause inside the
    word), and the median gap between words."""
    plain, by_ending, gaps = [], {}, []
    for page in word_times['pages']:
        words = page['words']
        for i, w in enumerate(words):
            n = letters(w['text'])
            if not n:
                continue
            kind = ending(w['text'])
            (plain if kind == 'none' else by_ending.setdefault(kind, [])).append((n, w['end'] - w['start']))
            if i + 1 < len(words):
                gaps.append(max(0.0, words[i + 1]['start'] - w['end']))
    xs = [p[0] for p in plain]
    mx, my = statistics.mean(xs), statistics.mean(p[1] for p in plain)
    slope = sum((x - mx) * (y - my) for x, y in plain) / sum((x - mx) ** 2 for x in xs)
    base = my - slope * mx
    extra = {kind: max(0.0, statistics.median(d - (base + slope * n) for n, d in pairs)) for kind, pairs in by_ending.items()}
    gap = statistics.median(gaps)
    # medians run short (long pauses are rarer but long): scale everything so the measured recording's own words,
    # timed this way, come out at its real length
    predicted = real = 0.0
    for page in word_times['pages']:
        words = [w for w in page['words'] if letters(w['text'])]
        predicted += sum(base + slope * letters(w['text']) + extra.get(ending(w['text']), 0.0) for w in words) + gap * (len(words) - 1)
        real += words[-1]['end'] - words[0]['start']
    return {'base': base, 'per_letter': slope, 'extra': extra, 'gap': gap, 'scale': real / predicted}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('script')
    parser.add_argument('measured')
    parser.add_argument('out')
    parser.add_argument('--pause-after', nargs='*', default=[])
    parser.add_argument('--default-pause', type=float, default=1.5)
    parser.add_argument('--slower', type=float, default=1.0)
    args = parser.parse_args()
    script = json.load(open(args.script))
    m = measure(json.load(open(args.measured)))
    longer = {int(k): float(v) for k, v in (item.split('=') for item in args.pause_after)}
    accent = script.get('accent_instruction', '')
    names = script.get('phonetic_names', {})

    t = FIRST_WORD_AT
    pages, pauses = [], {}
    for n, page in enumerate(script['pages']):
        text = page['text'].replace(accent, '').strip()
        for phonetic, plain in names.items():
            text = text.replace(phonetic, plain)
        text = re.sub(r'\.\.\.(?=\S)', '... ', text)   # "word...word" -> two words
        words = []
        first = t
        tokens = text.split()
        for i, token in enumerate(tokens):
            length = (m['base'] + m['per_letter'] * letters(token) + m['extra'].get(ending(token), 0.0)) * m['scale'] * args.slower
            words.append({'text': token, 'start': round(t, 3), 'end': round(t + length, 3)})
            t += length
            if i + 1 < len(tokens):
                t += m['gap'] * m['scale'] * args.slower
        last = t
        pages.append({'page': page['page'], 'name': page['name'], 'recording': None, 'estimated': True,
                      'recording_starts_at': round(first - 0.09, 3), 'first_word_at': round(first, 3),
                      'last_word_end_at': round(last, 3), 'words': words})
        if n + 1 < len(script['pages']):
            gap = longer.get(page['page'], args.default_pause)
            pauses[str(page['page'])] = gap
            t = last + gap
    seconds = t + TAIL_AFTER_LAST_WORD
    timeline = {
        'note': ('What this file is: an ESTIMATED chapter timeline, made by narration-tools/estimate_timeline.py from '
                 'the narration script before anything was recorded. Word lengths and pauses are measured from a real '
                 'recording of the same narrator. Replace it with the real timeline once the narration is recorded.'),
        'estimated': True,
        'measured_from': args.measured.split('/')[-1],
        'measurements': {k: (round(v, 4) if isinstance(v, float) else {kk: round(vv, 3) for kk, vv in v.items()}) for k, v in m.items()},
        'frames_per_second': FRAMES_PER_SECOND,
        'chapter_seconds': seconds,
        'chapter_frames': int(round(seconds * FRAMES_PER_SECOND)),
        'first_word_at': FIRST_WORD_AT,
        'pauses_after_page': pauses,
        'tail_after_last_word': TAIL_AFTER_LAST_WORD,
        'pages': pages,
    }
    json.dump(timeline, open(args.out, 'w'), indent=1)
    spoken = sum(p['last_word_end_at'] - p['first_word_at'] for p in pages)
    words = sum(len(p['words']) for p in pages)
    print(f'{len(pages)} pages, {words} words, {spoken:.0f} s of speech ({words / spoken * 60:.0f} words a minute), '
          f'chapter {seconds:.0f} s ({int(seconds // 60)}:{int(seconds % 60):02d}); saved {args.out}')


if __name__ == '__main__':
    main()
