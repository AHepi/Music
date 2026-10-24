# Runtime 0.2.0

## Artist workflow

1. In Object mode, select a local open top heightfield mesh. Set Receiving Surface. Use Make Starter Mask JSON.
2. In Blender's Text Editor, inspect the generated JSON. Supply explicit protected rectangles for foundations, hall/support footprints and areas that must stay unchanged; full-width path polylines for traffic; waterline; bank zones; contact/shelter zones; gravel and moss patches. Units are source-local metres.
3. Load JSON controls, adjust seed, detail scale, relief, densities, sizes, water/contact/shelter controls, and Build Retained Landscape. Different path widths remain unchanged unless Override All Path Widths is explicitly enabled.
4. Use Check Source / Coverage / View. Inspect the JSON Text named in the panel. Render both a hero view and a near view. The report separates geometry invariants, finite support tests and projected size estimates from artistic acceptance.
5. To change geometry, Read Active then Rebuild. This makes a new generation and hides the old one only after successful creation. Restore reveals the retained source and hides generated output; generated IDs remain available for inspection.

The source must be local, static, an upward open heightfield, one scene, no modifiers/shapekeys/constraints, positive uniform scale and no shear. The source itself is never remeshed or displaced. A modified copy receives relief. Every original polygon intersecting a protected rectangle, path capsule or source-water region has all vertices frozen, so its entire interior preserves source Z. This is conservative by up to one source polygon: a coarse receiver can suppress all relief. That suppression is reported; refine the receiving surface rather than weakening masks. Relief is an authored bank field, not erosion.

Generated pebble/cobble deposits are correlated groups with individual shape and coherent tone variation. Moss uses a closed, terrain-conforming low body with organic clipped contours and low crowns. Topology checks target upward surface winding and manifold body edges. Body cells intersecting protected traffic/support footprints are discarded, even when all their vertices lie outside the footprint. This is a finite mesh model; small occluded details and fine terrain curvature still require inspection.

## Live candidate scatter

Choose an explicit receiving mesh and a collection containing source meshes. Set a Text using `data/native_scatter.schema.json`, then Build Live Candidate Scatter. Unlike static landscape generation, this creates live native Geometry Nodes with Density, Traffic Width, Waterline, Damp Reach, Contact Influence and Seed sockets. Native behavior survives save/reopen without Python handlers or the add-on enabled.

Records contain x/y, scale and Euler rotation, traffic distance to a path centerline, habitat and contact weights, and preferably a unique stable id. Optional z is retained metadata; raycast determines actual height. Coordinates and all distances are receiver-local. Traffic Width is the forbidden centerline radius, not the landscape schema's full path width. Candidate radius is subtracted before the traffic comparison, so whole footprints receive a conservative margin.

Source objects must have identity local transforms and no parents; bake their dimensions into local mesh coordinates. The evaluated source bottom must be near Z0: minimum Z in [-15%, +2%] of evaluated height. Normalize deliberately rather than relaxing this guard. Source membership and geometry are retained by ID, not names. Bank member order is explicit; changing membership requires regeneration. Use stable record IDs to preserve per-candidate random values. When IDs are omitted, input indices are identities, so reordering changes them.

Before mutation, evaluated receiver loop triangles build a BVH. A conservative sphere bound derived from every evaluated source and candidate scale determines the probe radius. Center plus eight perimeter hits must exist and satisfy slope and tangent-plane residual limits. After embedding, a support gap over 0.035 local units for pebbles or 0.020 for moss/tufts rejects the candidate. These are finite initial samples, not a proof of full continuous contact or penetration. The audit detects subsequent receiving-surface or source-evaluation changes and asks for regeneration/recheck. Center grounding remains live after such edits. Disabling footprint checks is explicit and fails the qualification check.

Fixed ray origins avoid field-context reevaluation after Set Position. Instances align Z to receiving normals. Hosts parent to their receivers, so pose changes carry the scatter. A world-space adapter is required when input records are world-space but the receiving object is scaled; see the courtyard integration example.

## Planks and materials

Create Varied Planked Run generates a straight level supported top plane with cumulative nonuniform board widths, gaps, bounded corner losses and several coherent timber tones. Overall endpoints stay fixed. It is explicit generation, not a live curved bridge solver. The courtyard bridge adapter separately uses a structural tangent frame, then bounded stylistic twist; do not use style tilt to fix bearing contact.

Material-Specific Detail requires explicit Timber, Stone or Ceramic. Timber uses private bounded grain-aligned normal/stain detail plus a retained actual Boolean check. Stone makes an angular local fissure; ceramic makes bounded edge loss. Cutters parent to their receiver. No automatic material-name classifier or all-over generic noise is used. Thickness and scale matter; actual intersections need evaluated/render inspection.

Private Pigment Field uses the bundled full generated atlas for color only, with local grain axes. Each application loads a private Image and makes private shader copies; it does not repurpose an existing shared image or its colorspace. The timber detail group is also private, so an existing same-name group cannot substitute another shader.

Qualified Fabric Overlay supports the accepted Foundry material graph only and changes its color-overlay strength. Unsupported graphs reject before mutation. It does not claim arbitrary cloth generation. The historical narrow background palette recipe is preserved for provenance, not exposed as automatic palette correction.

Surface transactions preserve exact source mesh/material ID pointers and slot link modes, including multi-slot and shared DATA cases. Restore refuses source geometry/binding changes, unexpected receiver material bindings or outside modifiers rather than overwriting them. Source geometry digests cover vertex positions, polygons and polygon material indices, not UVs, arbitrary custom attributes or shader internals. Those originals remain retained, but those domains are not fully fingerprinted by the audit.

## Python API

Import `<installed_extension_module>.runtime.api` inside Blender. Use explicit object/collection pointers rather than searching scene names. Important calls:

- `validate(spec)`, `parse(json_text)`, `default_spec(bounds, seed)`
- `create_landscape(source, spec, name='Landscape', collection=None)`
- `rebuild_landscape(root, spec)`, `restore_landscape(root)`, `audit_landscape(root, camera=None)`
- `create_native_scatter(name, records, bank, receiver, collection, kind, controls=None, footprint_check=True)`
- `set_scatter_controls(host, **values)`, `audit_native_scatter(host)`
- `create_planks(length, width, count, seed, variation, gap, location=..., rotation=...)`
- `apply_detail(obj, family, seed, depth, strength, stain)`
- `apply_pigment(obj, slot=0, kind='timber', grain_axis='X', ...)`
- `apply_textile(obj, slot=0, strength=0)`, `restore_surface(obj_or_keeper)`, `audit_surface(obj_or_keeper)`
- Qualified `RoofSpec`, `StoneSpec`, create/update/pose/material-binding component APIs are re-exported from the earlier native courtyard library.

JSON is data only. Unknown keys, wrong types, booleans in numeric fields, nonfinite values, unsupported sources, invalid budgets and duplicate IDs are rejected. Native controls validate the complete socket schema before writing any requested values. Ownership-scoped rollback removes only a failing transaction's newly created native IDs.
