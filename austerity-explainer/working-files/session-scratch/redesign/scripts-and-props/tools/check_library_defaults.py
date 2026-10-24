# What this does: checks, without writing anything, that the pit village prop scripts still point at the
# pit village's library and list when given no settings, and that the settings switch them.
import os
import sys
sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/pit-village/props')
import prop_library as library
import scripted_kit as kit
from poly_haven_choices import load_choices
print('CHECK default library:', library.PROPS_FOLDER.split('film-kit/')[1], '| index:', library.INDEX_PATH.split('film-kit/')[1])
print('CHECK default scratch:', library.SCRATCH, '| surfaces:', kit.surfaces_folder(), '| pictures:', kit.pictures_folder())
pit = load_choices(None)
print('CHECK pit village list:', len(pit.CHOICES), 'models, limit', pit.TRIANGLE_LIMIT, ', has LIBRARY:', hasattr(pit, 'LIBRARY'))
left = library.take_folder_settings(['coal-tub', '--library', 'inflation-chapter-2-newcomers', '--scratch', '/tmp/x'])
print('CHECK after settings:', library.PROPS_FOLDER.split('film-kit/')[1], library.SCRATCH, kit.surfaces_folder(), '| left:', left)
chapter = load_choices('/home/user/Music/austerity-explainer/film-kit/paper-film/blender/inflation-chapter-2-newcomers/props/chapter_2_choices.py')
print('CHECK chapter 2 list:', [c[0] for c in chapter.CHOICES], chapter.LIBRARY, sorted(chapter.SET_SURFACES))
