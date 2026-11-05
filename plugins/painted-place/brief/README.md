# Place brief

What this is: everything a builder gets to make one place for the film, and nothing else. It replaced the `painted-place` plugin's dressing code as the way the look transfers (decision 62, 3 November 2026): the pictures and the page carry the look; the builder's own judgment does the rest, including where every thing goes. Since decision 65 it also carries a store of ready parts, tools and materials the builder may pick from; nothing in the store places itself. It lives inside the plugin (`plugins/painted-place/brief/`) so an install carries it.

| File | What it is |
|---|---|
| `Brief.md` | The words a builder gets, and how a place is built with this folder |
| `The look.md` | The target in words and numbers: what the reference pictures have in common |
| `reference/` | Seven pictures: three series paintings, two renders, and two places built from this brief that the owner approved |
| `Traps.md` | What has gone wrong for builders before, one line each |
| `measure.py` | Measures a picture against the look's bands (`python3 measure.py PICTURE`) |
| `Before you build.md` | What to look at and write down before building: the board, the material list, who uses the place, where wear sits, three sizes of shape |
| `boards/<request>/` | Real photographs of the kind of place asked for (public domain), one folder per request, with a `Board.md` |
| `surfaces/` | A shelf of 26 photographed surfaces (Poly Haven, CC0) with their real sizes, for the builder to lay on as it chooses |
| `Second pass.md` | The brief for a second builder that dresses a finished place: surfaces, wear, the things people left |
| `Third pass.md` | The brief for a third builder, when the most detail is asked for: the buildings' faces and the middle distance |
| `Closer to the picture.md` | The brief for one more builder when the owner asks for a place to come closer to a picture they sent: the differences closed biggest first |
| `store/` | Ready parts (a tent, a gun, a lantern, a hut, a shop front, a chimney stack, a stone lantern, an arched bridge, a maple, an azalea...), tools that make a thing from a line or a shape you give (a duckboard walkway, cobbles along any curve, a kerb, brick or stone walls filling a plane, a tiled roof, paper screens, a veranda, a slab path, a bamboo fence, lapped boards, stonework, a slate roof with gutters, a downpipe, stains and weathering, a puddle, a dry-stone wall, a hedge, the ground and its tracks, a low golden sun, far hills, a baked stand-in for a detailed part), ready materials (photographed stone and brick, the street's 45, the shelf's 31, the made ones) and a finishing step; see `store/Store.md` |

How lessons travel: a good new picture joins `reference/`; a fault joins `Traps.md`; a new kind of place gets a board; a new surface joins the shelf; a good new part, tool or material joins the store. No code that decides where things go is added anywhere.

## Traps

- The originals here are frozen. A builder gets a copy.
- `measure.py` checks colour and light only; it cannot see a wrong shape. Look at every picture.
- The store's tools and parts find the shelf and the materials by their place inside this folder; copy the whole folder, never the store alone.
