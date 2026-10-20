# What is in this folder and what was changed (plain words)

This folder is a COPY of the current slate recipe, made for the "generated mask stamps" test. The original (recipes/slate_layers/) was only read, never written to.

Copied on 20 October 2026 at 13:12 (UTC). A fingerprint (SHA-256 checksum) of every copied file is in `COPIED_FROM_SLATE_checksums.txt`. At 14:21 the same
check was run again against the original folder and every file still matched, so the original had not changed while the test ran.

## What was changed in the copy
| file | change |
|---|---|
| `layers/stamps.py` | NEW. The helper that places one stamp from the atlas picture onto a slate (see the notes file). |
| `layers/moss.py` | a setting `moss.mask_mode` ('nodes', 'stamps' or 'both') and five stamp controls were added; in 'stamps' mode the stamp mask replaces the node-made growth mask. See `changes_moss.diff`. |
| `layers/damage.py` | the same for the flaked edges: `damage.mask_mode` and five stamp controls; only the lower-edge flakes are replaced. See `changes_damage.diff`. |
| every other file (`recipe/slate_recipe.py`, `recipe/settings.json`, `layout.py`, `colour_and_fade.py`, `outline_and_shadow.py`, `combine.py`, `layer_interface.py`) | NOT changed (byte for byte the same as the original). |

## Proof that the copy, left in its normal mode, is the same slate
With `mask_mode` left at its default ('nodes') the copy builds the old node graph (only some unused extra sockets are added). Baked at 512 dots next to the
original recipe, colour and height differ in 0 dots (largest difference 0.00000). Pictures: `../work/same/`.

## How to switch the stamps on
Settings (in `recipe/settings.json` or passed as parameters; the exact sets used in the test are in `../compare/variant_settings.json`):
- `"moss.mask_mode": "stamps"` and `"moss.stamp_atlas": "<full path>/moss_C_atlas.json"`  (moss from stamps)
- `"damage.mask_mode": "stamps"` and `"damage.stamp_atlas": "<full path>/chips_C_atlas.json"`  (chips from stamps)
- the value `"both"` means: node-made mask times stamp mask (a dot needs both to be painted).
