"""What this file does (plain words): in the checking copy of the film kit (kit_check/, made by make_kit_copy.sh AFTER the wet street went into the film),
adds three copies of the lockout scene that can be told which painting files to load from the address (?painting=NAME&behind=NAME), because the real scene
always loads lockout-painted.jpg and lockout-behind.jpg (now the wet ones) and the proof needs the DRY alternates drawn with the new stage file:
  lockout-oldlook-hook.js : the lockout scene exactly as it was before this job (taken from kit_before, the film as it was), plus the name hook.
                            Drawn with the NEW stage file and the dry alternates it must give the same pictures, dot for dot, as the old stage file did:
                            this proves the stage change alone (the new switch left off) changes nothing.
  lockout-newlook-hook.js : the lockout scene as it is in the film now (toe 1, frame edge 0.25), plus the name hook. With the dry alternates it shows
                            what the dry street looks like under the new look (what a rename back to the dry files alone would give).
Only the one line that loads the two paintings is changed, and a note is put at the top. Run: python3 -I make_hook_scenes.py
"""
import os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = "loadTexture(`${SET}/lockout-painted.jpg`), loadTexture(`${SET}/lockout-behind.jpg`)"
B = "loadTexture(`${SET}/${new URLSearchParams(location.search).get('painting') ?? 'lockout-painted.jpg'}`), loadTexture(`${SET}/${new URLSearchParams(location.search).get('behind') ?? 'lockout-behind.jpg'}`)"
for source, target, note in (
    (W + '/kit_before/paper-film/scenes/lockout-test.js', W + '/kit_check/paper-film/scenes/lockout-oldlook-hook.js', "the film's lockout scene as it was BEFORE the wet street (old look: toe off, frame edge 0.30)"),
    (W + '/kit_check/paper-film/scenes/lockout-test.js', W + '/kit_check/paper-film/scenes/lockout-newlook-hook.js', "the film's lockout scene as it is NOW (new look: toe 1, frame edge 0.25)")):
    s = open(source).read()
    assert s.count(A) == 1, source
    s = "// NOTE (plain words): checking copy of " + note + ", with ONE change: the two painting file names can be given in the address (?painting=NAME&behind=NAME). Made by wet_lockout_film/tools/make_hook_scenes.py.\n" + s.replace(A, B)
    open(target, 'w').write(s)
    print('wrote', target)
