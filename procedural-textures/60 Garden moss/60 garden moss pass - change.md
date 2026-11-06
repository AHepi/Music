# The change

## What the owner asked for

The owner's last words, after seeing the rocks pass: "Ok. I meant the rocks with moss. Not the pavement lol. Those are still lacking a lot of detail"

So: the mossy rocks need much more detail. The path's paving stones stay as they are. The earlier owner's word still holds for the rocks: "They need to be procedurally generated in a particle system. And better textured". And for every builder: "Please remind the builders to use PBR wherever possible. It save in space and compute."

In the owner's picture the mossy rocks are craggy grey granite with thick, soft moss cushions sitting on their tops and in their cracks, spilling over the edges, with pale lichen spots on the bare stone, small plants and ferns where they meet the soil, and a basin of rough stone with moss round its rim. In the earlier picture the moss is only a flat green colour painted on smooth lumps.

## Where it shows in the place

Every rock that carries moss, near and far:

1. The stone basin under the bamboo spout (right of the path; the biggest mossy thing in both views).
2. The big rock beside the basin, the basin's front stone and the 14 small rocks round the basin's foot (near the eye; large in the close view).
3. The two flat stones in the near water (before the stone lantern, and beside the path).
4. The stone lantern's seat and its mound of three boulders.
5. The 120 boulders along the pond's bank and the channel's.
6. The single rocks (right bank, far bank, both ends of the bridge).
7. The pads under the veranda's posts (thin moss, mostly hidden by the deck's edge).

Not changed: the path's paving stones and the stepping stones (the owner: "Not the pavement"), the stone lantern itself (a carved lantern, not a rock), the layout, the camera, the light, everything else.

## How I will make it

The store now has real moss, made for exactly these words (decision 90):

- Real moss on every mossy rock: soft cushions with thickness, thick on the tops and in the hollows, thinning to nothing at frayed edges and creeping over the rims; on them a pile of tiny tufts laid by Blender's particle system; greens from young to old with dry tips; laid over the shelf's photographed moss (PBR). Pale lichen crusts on the bare stone. This is the rocks tool's `moss_style='cushions'`; the rocks stay rule-made and laid by the particle system as before.
- The stone basin: `moss.grow` gives it the same real moss on its rim, its top and its foot.
- Where the rocks meet the soil: `moss.feet` adds moss spilling onto the soil, grass tufts and a few ferns at the biggest rocks, as in the owner's picture.
- Better stone: real bumps from the photograph's height picture on the rocks near the eye and on the lantern's mound, the photograph's relief kept strong.

First I draw the earlier script once, small, with the fresh kit (the store has grown; the earlier script may already draw differently), and compare it with its picture. Then one change at a time, measuring every picture and looking at it at full size beside the earlier one.

## Traps

- The fresh kit already changes what the earlier script draws: the store's rocks tool now grows real moss cushions by default, so the earlier script drawn today shows lime cushions it never showed the owner. Set the moss options in the script, not by the tool's default.
- The moss tool's `grow` remakes a stone as even small faces first, which needs a closed shape: on the carved basin (open underneath) it grew almost nothing until it was given a closed copy.
- The moss tool's `feet` sets its ferns at a random side of the biggest rocks: twice one landed on the path (in front of the bucket, then at the basin's front stone). Ferns near the path are set by hand.

# The second change (the owner's words while this pass was being made, 13:31 to 13:33)

The owner's words, in order: "Is Eevee rendering faster?" "The pools of water on the pavement also need to be semi transparent. Right now, it looks like a liquid mirror" "Once done, do one final render in Cycles." "Also, are the rocks using PBR? That should be the standard for textures." The session answers the two questions; the job grows by one change: the pools of water on the path made semi transparent, keeping the moss work.

## Where it shows in the place

- The pools in the slabs' hollows along the whole path (the long one that mirrors the hanging lantern and the smaller ragged ones), in both views; in the close view they are the biggest things in the picture.
- The store puddle on the path beside the veranda (at the path's left edge, near the eye).
Not the pond, not the basin's water (neither is on the pavement).

## How I will make it

The pools are now an opaque dark surface with a strong mirror (a very high reflecting strength), so nothing under the water shows. I will make the water let the stone under it show through, and reflect only part of the light, more at a low glancing look and less looking down (as real water does), so the slab's stone, its colour and its cracks show through the water while the sky and the lantern's light still shine on it. The water will also thin out towards its edge, where a pool is shallow, so no hard cut edge of mirror is left. Light passes through the water to the stone below (a see-through surface rather than one that bends the light, so the stone under it stays lit by the lamps). I check it in small quick pictures of the close view first, then draw both views at full size in Cycles.
