"""
What this file does:
Makes a judging packet: one folder a fresh model can judge from without knowing who built the picture or how.
The packet holds the candidate picture, the reference pictures, "The look.md", the person's request in their own
words, the measures and their verdicts, and the rubric the judge answers. The builder hands the judge the packet
folder and nothing else.

    python3 judge.py CANDIDATE.png --out PACKET_FOLDER --request "the person's words, exactly" [--also OTHER.png ...]

Then start the blind-judge agent with only this line: "Judge the packet at PACKET_FOLDER."
The judge's answer is saved by the builder as PACKET_FOLDER/verdict.md and acted on in one fix pass.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure  # noqa: E402

RUBRIC = """# Judge this packet

You are judging two things about the picture `candidate.jpg`:

- **the look:** does it belong with the pictures in `reference/` and the look described in `The look.md`?
- **the request:** does it show what the person asked for, in their own words in `The request.txt`? A picture
  that has the look but not the place asked for has failed; so has the place without the look.

You do not know who made it or how, and you do not need to. Look at the reference pictures first, then the
candidate, at full size, then read the request. Read `measures.json` last: it is a check on colour and light,
not on shapes.

Answer in this order, in plain words a non-technical person can act on:

1. **Verdict on the look:** one of "yes", "nearly", "no" - does the candidate belong with the references?
2. **Verdict on the request:** one of "yes", "nearly", "no" - would the person who wrote `The request.txt`
   recognise their place in it? Name, in one sentence, what a viewer would say the picture shows.
3. **Fixes, most visible first.** At most seven, for the look and the request together. For each:
   - what a viewer sees (one sentence, point at where in the frame),
   - what to change (one sentence),
   - which kind of change it is: a DIAL (exposure, window light, haze, sky strength, finish mix, camera
     height or lens: things the look stage sets), a SHAPE (something built wrong or missing: a balloon-shaped
     smoke, a floating part, a blob tree, an empty foreground, toy-like props), a SURFACE (a clean new
     material where an old one belongs; missing wet, grime, moss, weeds, rust, peeling paint, litter where
     things collect), or a REQUEST (something the request calls for that the picture lacks or gets wrong:
     the wrong place, period, climate, building or use).
4. **What already works** (two or three sentences), so the fix pass does not undo it.

Judge the look against these points from `The look.md`: dark picture with rare precious light; teal-blue shadow
against amber light; one dominant light with a visible consequence in the air; haze between near and far;
everything old and used (wet, stained, mossy, weathered, with small things gathered where things collect: at wall
feet, in gutters, along a tide line); tall frame with single-point perspective, a centred hero, a detailed
foreground along the bottom and the eye at standing height; scale from objects not people; brushy but legible
finish. Judge the request by what a viewer who reads only the request would expect to see. Where the two pull apart,
the request decides the period, the place, the climate and what the building is; the look decides the light, the
colour, the air, the wear and the finish (a request for today's Samoa is today's Samoa, at blue hour, old and used).

Do not praise. Do not list rules the candidate follows. Do not suggest a method, a tool or a number of samples;
say what the viewer should see instead. If the measures and your eyes disagree, say so and trust your eyes.
"""


NO_REQUEST = ('(The builder gave no request. Judge the look only, and say under the request verdict that there was '
              'nothing to judge it against.)')


def build_packet(candidate, out_folder, also=(), request=None):
    out = Path(out_folder)
    (out / 'reference').mkdir(parents=True, exist_ok=True)
    from PIL import Image
    Image.open(candidate).convert('RGB').save(out / 'candidate.jpg', quality=95)
    for index, extra in enumerate(also, start=2):
        Image.open(extra).convert('RGB').save(out / f'candidate-{index}.jpg', quality=95)
    for picture in sorted((HERE / 'reference').glob('*.jpg')):
        shutil.copy(picture, out / 'reference' / picture.name)
    shutil.copy(HERE / 'The look.md', out / 'The look.md')
    numbers = measure.measure(Image.open(candidate))
    judged = measure.verdicts(numbers)
    (out / 'measures.json').write_text(json.dumps({
        'bands': measure.BANDS,
        'candidate': {'numbers': numbers, 'verdicts': judged,
                      'dials': {n: measure.dial_for(n, v) for n, v in judged.items() if v != 'inside'}},
    }, indent=2))
    (out / 'Judge this packet.md').write_text(RUBRIC)
    (out / 'The request.txt').write_text((request or NO_REQUEST).strip() + '\n')
    return out


def main(argv):
    parser = argparse.ArgumentParser(description='Build a blind judging packet.')
    parser.add_argument('candidate')
    parser.add_argument('--out', required=True)
    parser.add_argument('--also', nargs='*', default=[], help='more pictures of the same place (other views)')
    parser.add_argument('--request', help="the person's request, in their own words, exactly as they wrote it")
    args = parser.parse_args(argv)
    if not args.request:
        print('note: no --request given; the judge can only judge the look')
    out = build_packet(args.candidate, args.out, args.also, request=args.request)
    print(f'packet ready: {out}')
    print(f'give the blind-judge agent only this: "Judge the packet at {out}."')


if __name__ == '__main__':
    main(sys.argv[1:])
