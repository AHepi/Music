"""
What this file does:
Makes a judging packet: one folder a fresh model can judge from without knowing who built the picture or how.
The packet holds the candidate picture, the reference pictures, "The look.md", the measures and their verdicts,
and the rubric the judge answers. The builder hands the judge the packet folder and nothing else.

    python3 judge.py CANDIDATE.png --out PACKET_FOLDER [--also OTHER.png ...]

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

You are judging whether the picture `candidate.jpg` belongs to the look shown by the pictures in `reference/`
and described in `The look.md`. You do not know who made it or how, and you do not need to. Look at the
reference pictures first, then the candidate, at full size. Read `measures.json` last: it is a check on
colour and light, not on shapes.

Answer in this order, in plain words a non-technical person can act on:

1. **Verdict:** one of "yes", "nearly", "no" - does the candidate belong with the references?
2. **Fixes, most visible first.** At most seven. For each:
   - what a viewer sees (one sentence, point at where in the frame),
   - what to change (one sentence),
   - which kind of change it is: a DIAL (exposure, window light, haze, sky strength, finish mix, camera
     height or lens: things the look stage sets), a SHAPE (something built wrong or missing: a balloon-shaped
     smoke, a floating part, a blob tree, an empty foreground), or a SURFACE (a clean new material where an
     old one belongs).
3. **What already works** (two or three sentences), so the fix pass does not undo it.

Judge against these points from `The look.md`: dark picture with rare precious light; teal-blue shadow against
amber light; one dominant light with a visible consequence in the air; haze between near and far; everything
old and used; tall frame with single-point perspective, a centred hero, a detailed foreground along the bottom
and the eye at standing height; scale from objects not people; brushy but legible finish.

Do not praise. Do not list rules the candidate follows. Do not suggest a method, a tool or a number of samples;
say what the viewer should see instead. If the measures and your eyes disagree, say so and trust your eyes.
"""


def build_packet(candidate, out_folder, also=()):
    out = Path(out_folder)
    (out / 'reference').mkdir(parents=True, exist_ok=True)
    shutil.copy(candidate, out / ('candidate' + Path(candidate).suffix.lower()))
    for index, extra in enumerate(also, start=2):
        shutil.copy(extra, out / f'candidate-{index}{Path(extra).suffix.lower()}')
    for picture in sorted((HERE / 'reference').glob('*.jpg')):
        shutil.copy(picture, out / 'reference' / picture.name)
    shutil.copy(HERE / 'The look.md', out / 'The look.md')
    from PIL import Image
    numbers = measure.measure(Image.open(candidate))
    judged = measure.verdicts(numbers)
    (out / 'measures.json').write_text(json.dumps({
        'bands': measure.BANDS,
        'candidate': {'numbers': numbers, 'verdicts': judged,
                      'dials': {n: measure.dial_for(n, v) for n, v in judged.items() if v != 'inside'}},
    }, indent=2))
    (out / 'Judge this packet.md').write_text(RUBRIC)
    return out


def main(argv):
    parser = argparse.ArgumentParser(description='Build a blind judging packet.')
    parser.add_argument('candidate')
    parser.add_argument('--out', required=True)
    parser.add_argument('--also', nargs='*', default=[], help='more pictures of the same place (other views)')
    args = parser.parse_args(argv)
    out = build_packet(args.candidate, args.out, args.also)
    print(f'packet ready: {out}')
    print(f'give the blind-judge agent only this: "Judge the packet at {out}."')


if __name__ == '__main__':
    main(sys.argv[1:])
