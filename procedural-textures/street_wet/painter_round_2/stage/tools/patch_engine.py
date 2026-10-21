"""What this file does (plain words): sets the COPY of the film's stage drawing file (kit_copy/paper-film/stage/cinema-stage.js) to one of three states, always starting again from the film's own file
(read only, never changed), so the states can be switched cleanly:
  original    the film's file exactly as it is
  diagnostic  the film's file plus two new finishing-look values, used only to find out which step of the finish causes how much: curve (1 = the film's filmic curve is used, 0 = it is left out altogether) and toe (see below)
  fix         the film's file plus ONE new finishing-look value, toe (0 = the film's curve exactly as it is today, the default; 1 = the filmic curve may still brighten but may no longer darken: where the curve would
              make a value darker than it was painted, the painted value is kept). Nothing changes for any scene that does not ask for it.
The edit is these lines of cinema-stage.js (the "finish" pass):
  shader:  c = aces(c);   becomes   vec3 filmicValue = aces(c); c = mix(filmicValue, max(filmicValue, c), toe);        (diagnostic: c = mix(c, mix(filmicValue, max(filmicValue, c), toe), curve);)
  plus     uniform float toe;  in the shader's list,  toe: { value: 0 }  in its settings,  toe: 0  in DEFAULT_LOOK,  and  u.toe.value = look.toe;  where the other look values are handed over.
Run: python3 -I tools/patch_engine.py original|diagnostic|fix
"""
import os, sys, shutil
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILM = '/home/user/Music/austerity-explainer/film-kit/paper-film/stage/cinema-stage.js'
TARGET = os.path.join(HERE, 'kit_copy/paper-film/stage/cinema-stage.js')
mode = sys.argv[1]
s = open(FILM).read()
def once(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)
if mode in ('diagnostic', 'fix'):
    shader_new = ('vec3 filmicValue = aces(c);\n    c = mix(filmicValue, max(filmicValue, c), toe);' if mode == 'fix'
                  else 'vec3 filmicValue = aces(c);\n    c = mix(c, mix(filmicValue, max(filmicValue, c), toe), curve);')
    once('    c = aces(c);\n', '    ' + shader_new + '\n')
    once('uniform float vignette; uniform float grain;', 'uniform float toe; ' + ('uniform float curve; ' if mode == 'diagnostic' else '') + 'uniform float vignette; uniform float grain;')
    once('vignette: { value: 0.32 }, grain: { value: 0.035 },', 'toe: { value: 0 }, ' + ('curve: { value: 1 }, ' if mode == 'diagnostic' else '') + 'vignette: { value: 0.32 }, grain: { value: 0.035 },')
    once('  vignette: 0.32, grain: 0.035, fringe: 0.006, lift: 0.015, fade: 0,\n', '  vignette: 0.32, grain: 0.035, fringe: 0.006, lift: 0.015, fade: 0,\n  toe: 0,' + (' curve: 1,' if mode == 'diagnostic' else '') + '   // toe: 0 = the filmic curve as it always was; 1 = the curve may brighten but never darken a value (dark painted values stay as painted)\n')
    once('u.vignette.value = look.vignette;', 'u.toe.value = look.toe; ' + ('u.curve.value = look.curve; ' if mode == 'diagnostic' else '') + 'u.vignette.value = look.vignette;')
    once('//    colour fringing at the edges, words and charts on top, dark edges and grain. Output is sRGB.\n', '//    colour fringing at the edges, words and charts on top, dark edges and grain. Output is sRGB.\n//    look.toe (0 by default = the curve as it always was): 1 = the filmic curve may still brighten a value but never darkens one, so dark painted values stay as painted (wet street test, round 2).\n')
else:
    assert mode == 'original'
open(TARGET, 'w').write(s)
print('cinema-stage.js in the copy is now:', mode)
