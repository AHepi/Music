import json, re
UNITS = {'percent', 'cent', 'cents', 'year', 'years', 'month', 'months', 'week', 'weeks', 'day', 'days', 'hour', 'hours',
         'minute', 'minutes', 'dollar', 'dollars', 'pound', 'pounds', 'yen', 'marks', 'times', 'hundred', 'thousand', 'million',
         'billion', 'billions', 'trillion', 'in'}
SMALL = {'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'}
TEENS = {'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'}
TENS = {'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'}
BIG = {'hundred', 'hundreds', 'thousand', 'thousands', 'million', 'millions', 'billion', 'billions', 'trillion', 'trillions'}
FRACTIONS = {'half', 'quarter'}
CHANGE = {'double', 'doubled', 'doubles', 'triple', 'tripled', 'quadruple', 'quadruples', 'quadrupled', 'halve', 'halved'}
NUMBER = SMALL | TEENS | TENS | BIG | {'zero', 'point', 'percent'} | FRACTIONS
def tokens(text):
    return re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?%?", text.lower().replace('-', ' '))
def figures(text):
    toks = tokens(text)
    found, i = [], 0
    while i < len(toks):
        t = toks[i]
        if re.match(r'^\d', t) or t in NUMBER or t in CHANGE:
            j = i + 1
            while j < len(toks):
                if toks[j] in NUMBER or re.match(r'^\d', toks[j]):
                    j += 1
                elif toks[j] in ('and', 'a', 'of', 'in') and any(t in NUMBER for t in toks[j + 1:j + 3]) and not (toks[j] == 'and' and toks[j + 1] in SMALL | TENS and toks[j - 1] in SMALL):
                    j += 1
                elif toks[i] == 'one' and j == i + 1 and toks[j + 1:j + 4] == ['in', 'a', 'hundred']:
                    j += 1
                else:
                    break
            run = toks[i:j]
            nxt = toks[j] if j < len(toks) else ''
            prev = toks[i - 1] if i else ''
            keep = True
            if len(run) == 1 and run[0] in SMALL:
                # a small count of things ("two factories", "no one", "one reason") is not a figure; a count with a unit is
                keep = nxt in UNITS or (j + 1 < len(toks) and toks[j] not in ('of',) and toks[j + 1] in ('dollar', 'dollars', 'percent'))
            if run == ['point'] or run == ['percent']:
                keep = False
            if keep:
                found.append(' '.join(run) + (' ' + nxt if nxt in UNITS and nxt not in run else ''))
            i = j
        else:
            i += 1
    return found
for f, rec in (('old-chapter-2-narration-script.json', [0,3,0,3,7,3,6,3,5,7]), ('newcomer-narration-script.json', None)):
    d = json.load(open('/home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/script/' + f))
    tot = 0
    for p, page in enumerate(d['pages']):
        text = page['text'].replace(d['accent_instruction'], '')
        fs = figures(text)
        tot += len(fs)
        print(f[:3], page['page'], len(fs), rec[p] if rec else '', fs)
    print('TOTAL', tot)
