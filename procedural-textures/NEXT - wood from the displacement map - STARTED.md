# Started 20 October about 09:00 - wood from the displacement map

What the person said: "Maybe the wood is going to need the displacement map. But then procedurally generate more non repeating surface with it. Because it's not good."

What is being done (folder recipes/wood_from_displacement/): for WOOD ONLY, the uploaded wood displacement map is allowed as the source material. A Blender
recipe lays out rows of boards and gives each board its own random window of the map (random offset along the grain, flips, small tone changes), so the
default tile repeats without a seam and bigger areas (2 x 2, 4 x 4) never visibly repeat. Main colour is made from the height; a comparison version samples
the uploaded colour map with the same arrangement. Steps: research (how people do this in Blender 5.x, small tests), build, a fresh-eyes look check and an
honesty check, one fix round if needed. Helpers: Sonnet 5.5 at extra-high effort.

The wood reuse trial (reuse_trials/wood/, shared slate layers, picture as a guide only) keeps running: it answers the other question, "how much of the tools
can be used on the other textures".

## Added about 09:20
The person added: "And the material map." Taken to mean the uploaded wood colour map (the painted material picture of the same boards). The job was restarted
(it had only just begun) so that the MAIN version samples the colour map and the displacement map together with the same arrangement; the comparison version
makes colour from height instead. The normal is made from the sampled height (the uploaded normal map is not sampled, because a flipped board would make its
slopes point the wrong way) and compared with the uploaded normal as a check. Guides renamed "08 ... wood from your displacement and colour maps ...".
