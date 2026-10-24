"""Scratch (views-and-models helper): runs a saved copy of a place's assemble script as if it stood at its real path (so
its own imports and folders resolve), then nothing else; later --python scripts see the dressed scene. The same trick
the round 5 W4 helper used (plates_small.py). Use:
  blender -b BASE.blend --python run_script_as.py --python NEXT.py -- --script COPY.py --as REAL/assemble_x.py [their options]"""
import sys

argv = sys.argv[sys.argv.index('--') + 1:]


def option(name):
    return argv[argv.index(name) + 1]


script, real = option('--script'), option('--as')
sys.argv = [real] + sys.argv[1:]
namespace = {'__name__': '__main__', '__file__': real}
exec(compile(open(script).read(), real, 'exec'), namespace)
print('run_script_as: ran', script, 'as', real, flush=True)
