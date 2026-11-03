# 46 Pictures-only builders: three places

What this folder is: three places built by fresh Sonnet builders that had only the five reference pictures, the one-page look description (`plugins/painted-place/look/The look.md`) and Blender, no plugin (log 46 in the project story; decision 60). Each brief is the tea room builder's brief from the tea house test word for word, with only the request, the folder and the clock changed.

| Request (your words) | Ran | Finished | Picture | Draw of the final |
|---|---|---|---|---|
| "a suburban townhouse" | 09:53 to 11:15 | 10:43 | `46 Townhouse - final.png` | 540 x 960, 128 samples, 344 s |
| "a mine in the desert" | 10:53 to 12:15 | 11:47 | `46 Desert mine - final.png` | 540 x 960, 64 samples, 181 s |
| "a military base" | 11:54 to 13:20 | 12:45 | `46 Military base - final.png` | 540 x 960, 128 samples, 312 s |

One after another, so each had the whole machine (2 processors). Each left `render_final.py`, which draws its whole scene and finish (`python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png`); none was redrawn at full size. `46 All three side by side.jpg` puts them together. Each builder's own report is here.

## What they had in common

- All three set their place in Britain around 1915, at dusk, with one low light and small warm lights answering it: the look page asks for that period and place.
- All three wrote their own stand-in for the plugin's measuring tool and tuned until the reference pictures fell inside the bands.
- All three hit the same early faults: lamps whose own glass or casing blocked their light; haze far too thick; puddles that read as black holes or pale paper; the ground reading as snow or tin.
- All three made their own painted finish in code or in Blender's compositor (two painted smoke or rain on afterwards; one left smoke and rain out for fear of balloon shapes).

## Traps

- The look page fixes the period (Britain around 1915): a request like "suburban townhouse" comes out as a Victorian terrace, a desert mine as a pithead in the desert. Say the period in the request if you want another.
- These builders saw the repository's rules file and the owner's saved preferences, as every helper does; one listed its techniques for the plugin because of that file.
