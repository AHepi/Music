# NEXT PHASE - STARTED (first note said "don't start that yet"; then the person answered: slate first, layers inside the recipe, the picture only as a guide; the brief is "SLATE LAYERS BRIEF - pure procedural, layers inside the recipe.md")

Helpers working on the six surface builds: ignore this file. It is a note for later.

## What the person said (after seeing the slate build)
"The match is close enough. For the full procedural effect, the agent will need to keep the colour and fading, the damage and the moss patterns on
separate layers. But don't start that yet."

## What I take it to mean (to confirm before starting)
Today the slate picture is made as ONE painted layer: colour, fading, wear marks and moss all come from the same stamped patches, so none of them can
be changed on its own. For the full procedural effect each of these should be its own layer with its own settings and its own mask:
1. COLOUR AND FADING: the base tone of each piece and how it fades (for slate: the blue-grey of each slate and the downward streaking/fade).
2. DAMAGE: chips, worn edges, cracks, pale lichen-coloured breaks, scratches.
3. MOSS (growth): the olive moss and lichen patches and where they gather (in the references: in drips and low spots).
Each layer writes its own colour AND its own height (so the normal map shows damage and moss as real relief), and the layers are combined at the end.
Then a person can make "the same slate, twice as mossy, half as damaged, more faded" by turning one setting, and a larger set of surfaces can share
the same layers (moss from the slate moss layer on brick, damage layer reused on wood...).

## Open questions for the person (ask when starting)
* Which surfaces first (slate again, or all six)?
* Should the layers be separate pictures (masks and height per layer saved as files) as well as one combined picture, or only separate inside the recipe?
* Is it still fine to fit each layer's description from the reference (analyse -> describe -> generate), or should the layers now be made without
  fitting (pure procedural with settings you can change)?

## Plan sketch (not started)
Analyse each reference into the three layers (separate colour families and patch kinds by measured rules), describe each layer with its own compact
description and settings, generate each layer as its own Blender node group with its own mask, combine, compare dot-for-dot with the reference again (the
combined result must stay 'close'), then prove independence: change one layer's setting and show the other layers do not change.
