# About this example: the house sample

What this is: a note on why the house sample is in the kit, so that nobody copies its look by mistake.

**The person rejected this look.** The house sample put each chapter inside one cut-away doll's-house building, with
painted pages in its rooms. When the person saw the sample film they said: "It looks terrible. The 3d looks fantastic
though." (the austerity project's Decisions.md, item 33). What they liked was the real 3D: rooms and places the camera
moves through without tearing. That is what the later work built on (the pit village street, the Works, the
built-and-painted places of skill `build-and-paint-a-place`).

**Why it is still here.** It is kept only as a worked example of its code:
- cut-out pieces that pop up and fade smoothly (`setFading`, now also in `paper-film/scenes/cinema-kit.js`);
- rooms lit by their own glow, and cut-outs that go dark in a dark room;
- a street with its own light (a lit pavement and a lamp's pool of light), so people do not look as if they stand
  inside the lit rooms.

The files: `timeline.json` in this folder, and the page files in `paper-film/scenes/house-sample/` and
`paper-film/scenes/house-sample.js`.

**What not to do.** Do not copy its look (one cut-away building holding the whole chapter), and do not propose it to the
person again. If a new film needs rooms, build them as real 3D places the camera can move through.
