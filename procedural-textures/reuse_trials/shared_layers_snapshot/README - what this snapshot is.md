# Shared layers snapshot (read-only)

A frozen copy of the slate-in-layers layer files (`recipes/slate_layers/layers/*.py`) taken on 20 October before the slate look fixes started.
The reuse trials on brick, wood, metal, mud and gravel import the shared layers from HERE, so that changes made to the slate at the same time cannot
change the trials half-way. Do not edit these files: `checksums.txt` lists their fingerprints (sha256) and the checker compares them at the end.
To use them in a recipe: put `reuse_trials/shared_layers_snapshot/layers` at the front of `sys.path`, then `import layer_interface, colour_and_fade, damage, moss, outline_and_shadow, combine`
(and `layout` only if you want slate's own layout).
