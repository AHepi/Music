"""What this file does (plain words): writes down EXACTLY what would be changed in the real film project for the brightness fix, as two small patch files (the film project itself is not touched):
  the_fix/film_change_cinema-stage.js.diff     the stage's drawing file: one new finishing-look value, toe (default 0 = the film exactly as it is today)
  the_fix/film_change_lockout-test.js.diff     the lockout scene file: the lockout's look line gets toe: 1 and the dark frame edge goes from 0.30 to 0.25
Both are made by taking the film's own files, changing only those lines, and comparing. It also writes a test version of the lockout scene (kit_copy/paper-film/scenes/lockout-fixed-test.js: the film's file with exactly that change, plus the same
painting-name hook the other copies have), so one picture can be drawn with the REAL change (no address switch) and compared dot by dot with the picture drawn with the address switch (stills/after/wet_projector).
Run: python3 -I tools/make_real_film_patch.py
"""
import os, subprocess, shutil
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILM = '/home/user/Music/austerity-explainer/film-kit/paper-film/'
OUT = os.path.join(HERE, 'the_fix'); os.makedirs(OUT + '/patched/stage', exist_ok=True); os.makedirs(OUT + '/patched/scenes', exist_ok=True)
# 1. the stage file: the copy in its "fix" state is exactly the film's file plus the toe lines
shutil.copy(os.path.join(HERE, 'kit_copy/paper-film/stage/cinema-stage.js'), OUT + '/patched/stage/cinema-stage.js')
# 2. the lockout scene: the film's file with only the look line changed
s = open(FILM + 'scenes/lockout-test.js').read()
old = "glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.3, fade } };"
assert s.count(old) == 1
new = "glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.25, toe: 1, fade } };"
open(OUT + '/patched/scenes/lockout-test.js', 'w').write(s.replace(old, new))
def diff(a, b, name):
    r = subprocess.run(['diff', '-u', '--label', 'a/' + name, '--label', 'b/' + name, a, b], capture_output=True, text=True)
    return r.stdout
open(OUT + '/film_change_cinema-stage.js.diff', 'w').write(diff(FILM + 'stage/cinema-stage.js', OUT + '/patched/stage/cinema-stage.js', 'film-kit/paper-film/stage/cinema-stage.js'))
open(OUT + '/film_change_lockout-test.js.diff', 'w').write(diff(FILM + 'scenes/lockout-test.js', OUT + '/patched/scenes/lockout-test.js', 'film-kit/paper-film/scenes/lockout-test.js'))
# 3. the test scene: that same change plus the painting-name hook
t = open(OUT + '/patched/scenes/lockout-test.js').read()
a = "loadTexture(`${SET}/lockout-painted.jpg`), loadTexture(`${SET}/lockout-behind.jpg`)"
assert t.count(a) == 1
t = t.replace(a, "loadTexture(`${SET}/${new URLSearchParams(location.search).get('painting') ?? 'lockout-painted.jpg'}`), loadTexture(`${SET}/${new URLSearchParams(location.search).get('behind') ?? 'lockout-behind.jpg'}`)")
open(os.path.join(HERE, 'kit_copy/paper-film/scenes/lockout-fixed-test.js'), 'w').write("// NOTE (plain words): the film's lockout-test.js with ONLY the brightness fix written into its look line (toe: 1, vignette 0.25) plus the painting-name hook, to prove the real change gives the same picture as the address switch.\n" + t)
print(open(OUT + '/film_change_cinema-stage.js.diff').read()); print(open(OUT + '/film_change_lockout-test.js.diff').read())
