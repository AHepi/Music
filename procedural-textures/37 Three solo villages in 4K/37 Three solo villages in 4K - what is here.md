# 37 Three solo villages in 4K: what is here

What this file is: a map of the 4K pictures of the three villages built without the plugin, how they were made, and how to use the scenes.

You asked: "Yes can you draw the comparison of the three solo runs in 4k using the graphics cards. And take more photos. Stich them two side by
side at a time then return the zip folder inline."

## What is here

| Folder | What it holds |
|---|---|
| `side by side/` | 33 pictures, each two villages side by side (7704 x 2680 pixels): 11 views, three pairings per view, and a read-me. The same files as the zip you were sent. |
| `single pictures/` | The 33 single pictures (3840 x 2560 each), named `village_view.jpg`: `sonnet_` is Sonnet alone, `opus1_` is Opus alone first pass, `opus2_` is Opus alone second pass. |
| `scenes with the new cameras/` | Each village's scene with the six new cameras added and nothing else changed. The two Opus scenes are in three parts each (see below). |
| `how it was made/` | The drawing, card and side-by-side scripts, each village's per-view settings, the run log, the check sheets, and the camera-placing work for both layouts. |

## The three villages and the 11 views

- **Sonnet alone** (log 33), **Opus alone, first pass** (log 34), **Opus alone, second pass** (log 36).
- Views 01 to 05 are the five views each village was judged on, through that village's own cameras: from above, road at eye level, stable close,
  cottage close, road surface close-up.
- Views 06 to 11 are new: a second cottage, props close, into the empty stable stalls, a puddle at ground level, the road into the forest, the village
  from a low drone height. A camera was placed in each layout to show the same kind of subject. Opus's two passes share one layout, so they share
  the same six new cameras: those pairs are exact before-and-after pictures.

## How they were made

- Each village was drawn with its own light, brightness and samples from its own final pictures (Opus's second pass also with its own haze per view
  and its finer road surface for the two road views), at 3840 x 2560, with Cycles on rented RTX 4090 graphics cards, in 12 jobs of two or three views.
- Checks: every picture's brightness was compared with the village's own 1200 x 800 final picture of the same view (within about 3 levels out of
  255), a sheet of all 33 was looked at for mistakes, and a full-size crop was looked at for detail.
- Card time: about 1,370 seconds (23 minutes) for all 33 pictures.

## Joining the scenes in parts

GitHub refuses single files over 100 MB, so the two Opus scenes are in numbered parts. To join one back into a file that Blender opens:

- Mac or Linux, in a terminal in that folder: `cat "NAME.blend.part-1-of-3" "NAME.blend.part-2-of-3" "NAME.blend.part-3-of-3" > "NAME.blend"`
- Windows, in a command window in that folder: `copy /b "NAME.blend.part-1-of-3" + "NAME.blend.part-2-of-3" + "NAME.blend.part-3-of-3" "NAME.blend"`

Opus's second-pass scene without the new cameras is also saved whole, in one file, at
`../village-without-plugin-opus/second-pass/scene/village - Opus second pass (whole file).blend`.
