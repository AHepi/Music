# Recovery R01/R02: guidance for a recoverable painted workflow

Version 0.1.5 is a review candidate. These are attributed lessons from the frozen
R01/R02 independent reviews and source/QA records. They are manual guidance, not
new add-on operations, automatic repairs, accepted presets or a full-scene
construction system. The 0.1.5 task read the recorded evidence and checked its byte
identities; it did not rerun Blender, inspect image pixels anew or independently
rebuild the scenes. Ongoing R03 work is outside this evidence cut.

The exact uploaded 0.1.4 source remains intact. Runtime Python is identical after
only the release-version tuple, panel title and ADDON_VERSION substitutions; the
extension manifest differs only in version. The separate experimental Roof Course
Lab, settings, presets, preview snapshot 1.1 and conservative exclusions are
unchanged. All seven new recipes are unimplemented manual studies.

## Evidence entry points

- [R01 independent art review](../../qa/v0.1.5/evidence/recovery_run01/review/ART_REVIEW_R01.md)
- [R01 independent technical review](../../qa/v0.1.5/evidence/recovery_run01/review/TECHNICAL_REVIEW_R01.md)
- [R02 independent art review](../../qa/v0.1.5/evidence/recovery_run02/review/ART_REVIEW_R02.md)
- [R02 independent technical review](../../qa/v0.1.5/evidence/recovery_run02/review/TECHNICAL_REVIEW_R02.md)
- [R01 image identities](../../qa/v0.1.5/evidence/recovery_run01/review/ART_REVIEW_IMAGE_MANIFEST_R01.json)
- [R02 image identities and roles](../../qa/v0.1.5/evidence/recovery_run02/review/ART_REVIEW_IMAGE_MANIFEST_R02.json)
- [R02 technical image identities](../../qa/v0.1.5/evidence/recovery_run02/review/TECHNICAL_IMAGE_MANIFEST_R02.json)
- [New evidence source inventory](../../qa/v0.1.5/source_package_inventory.json)
- [External scene/image/archive identities](../../qa/v0.1.5/external_asset_inventory.json)

These links resolve in the source bundle. The small installable extension contains
this guide and the machine-readable provenance, but not source/QA reports or the
production images/scenes. Their paths are provenance, never runtime dependencies.
Image manifests record what the original reviewers viewed; that is not a claim of
fresh 0.1.5 visual review. No large recovery image archive is duplicated here.

R01 is a new reconstruction from earlier persisted scenes. It does not establish
exact restoration of lost later cycles. Historical cycle07/08 findings remain
scoped to their own source identities and are not silently applied as defects or
passes in the recovery scenes.

## 1. Flat pigment belongs to a real surface frame

R01 art review identified rounded camouflage-like islands on stone and overly
clean stripes on wood. R02 used generated flat pigment inputs, then judged them on
real geometry. The distinction matters: an attractive atlas is not a scene render
and cannot prove the look succeeded after mapping and illumination.

The independent R02 review checked all seven new street paint materials using the
saved R02_MaterialLocal UV layer and active face-used requirements on 1,082 changed
material owners. Three packed pigment images retained their exact PNG bytes and
sRGB interpretation. Their connected roles were Base Color and Toon Color, with
no pigment route into Normal, Height or Emission. The actual alternate-view/light
proof retained reveal, barrel and pavement depth with changing illumination. This
supports a bounded rejection of scene projection; it does not certify every
possible transform, view or deformation.

Keep the material-specific coordinate contracts explicit:

- Stone: actual face/return orientation, not a flat facade projection
- Masonry: a declared facade/assembly frame with continuity at the intended scale
- Barrels: circumference and lengthwise rest mapping, without restarting an
  identical stripe pattern on every stave
- Garments: declared garment-local mapping for the intended static pose
- Factory floor: saved R02_FloorPaint UVs on the 138 mapped slab owners
- Mine masonry: seven finite POINT/FLOAT_VECTOR R02_masonry_rest fields equal to
  their declared captured assembly-metre positions

The factory floor pigment also drives restrained Roughness mapping. Its inherited
Non-Color height input is separate. Calling the input “albedo pigment” must not
hide that second shader destination. The street no-height/no-emission finding is
specific to that graph, not a universal restriction on all material authoring.

Inspect active sockets, nested groups, face-used slots, field domain/type, finite
values, units and transform policy. Inherited paint_coords can use a different
frame from base local vertices. A raw nonzero difference is not itself a rest-field
failure. Keep original image bytes, prompts and role labels, and test the material
on the actual object before asserting success.

## 2. Stone marks and wood marks have different jobs

R02 removed the old rounded stone camouflage and improved interrupted lengthwise
barrel wear. The new limestone criticism is narrower: long uninterrupted axial
streaks and warm brown fields can read like timber. The alternate cool light makes
the surface grayer without necessarily changing that material reading.

A bounded next stone study would test short mineral/wear shapes, quiet chalky face
fields and selected broken chips along real stone edges. Those are proposed
manual directions, not verified R03 results or a universal preset. Keep useful
reveal depth and selected sharp masonry joints. Compare the actual surround under
production light and a meaningful alternate illumination.

Preserve the successful wood treatment. Do not repaint every material or add
all-over grit, bigger random islands, universal blur or global matte response.
Painted references can retain crisp edges, reflective water and metallic highlights.

## 3. Protected anchors do not prove manifold characters

R02 genuinely changed factory sleeves, cuffs, forearms, vests, palms and head/neck
planes. Calling these workers unchanged primitives would discard observed gains.
The shown near worker still has specific shoulder/sleeve-root, waist/hip and
paint-transition limitations, supported by matched close and side views. They are
not a universal anatomy judgment across the crowd; the separate original
character reference remains unavailable.

The independent preservation check covers 170 root/wrist/finger/boot hierarchy
owners. World transforms and protected finger/boot geometry are unchanged. Each
of four palms retains all 177 declared distal vertices exactly. Separately, all 80
new evaluated mesh components pass the recorded closed, contiguous, outward and
finite checks. These are different populations and different claims.

Six deliberately reshaped originals retain inherited split-face topology:

- Each of four palms: 880 nonmanifold/noncontiguous edges and 278 face-connected
  components, exactly matching R01
- Each of two heads: 6,240 such edges and 2,080 components, exactly matching R01

A positive signed sum on open faces does not demonstrate enclosed volume. No new
visible hole was established. Do not label these six inherited originals closed
production-ready manifold meshes, or treat a dark waist patch as proof of a hole.
If manifold delivery becomes a separate requirement, investigate targeted
retopology, careful welding or evaluated seam equivalence with anchor-preservation
checks. Do not weld indiscriminately during unrelated pigment edits.

Declare what geometry may change and what anchors must remain fixed before each
local form edit. Static equality and earlier sampled pose preservation do not
establish arbitrary skeletal garment deformation or physical cloth behavior.

## 4. Visible floor coverage includes more than the slab group

The selected R02 factory hero has an abrupt blue/ochre strip at its lowest roughly
1–2%. Both builder and independent saved-scene rays identify the visible owner:
Mesh_00139, authored as “V4 broad worn concrete and paint layers”, using material
M-9223371986422462674. It retains inherited UVMap and has no R02 floor mapping.
The immediately higher rays hit updated slabs Mesh_00021/Mesh_00022, using
M-9223372008132180543 with R02_FloorPaint.

The sampled R01/R02 hit positions and normals are identical. This is inherited
untreated coverage made conspicuous by the new floor treatment. It is not evidence
of a new floating floor, missing UVs, contact failure, clipping failure or image
composite. All 138 selected slabs can satisfy their own shader contract while
another visible floor owner remains outside that selection.

For a separately authorized correction, inspect the relevant visible faces and
give that owner a deliberate compatible material/coordinate treatment. Preserve
real geometry boundaries and the camera; do not assign a slab material to unrelated
geometry by name. Judge the actual transition in the unchanged hero view. The
correction is still proposed at this release’s R02 freeze and is not implemented
by 0.1.5.

[Owner ray evidence](../../qa/v0.1.5/evidence/recovery_run02/industrial/qa/factory_R02_edge_inspection.json)

## 5. A concentric pulley is not necessarily connected

R01’s eight upper torus rims were centered on their shafts but had no hub, web or
spokes between them. The measured radial gap was approximately 0.366999 m, and all
256 radial annulus rays were empty. The saved geometry, construction source and
candidate census established the issue; the small dark hero alone did not.

R02 added eight hubs and 48 spokes. The independent probe found common inward
solid-side witnesses between each shaft/hub and each spoke’s actual hub/rim ends.
All 208 signed nearest-surface checks were inward, with the least inward witness
about 4 mm from its tested surface. This closes that specific constructed-assembly
finding. It is not a load-bearing, stress-analysis or torque-transmission certificate.

Preserve centers, axes and belt planes. Use finite evaluated surfaces rather than
only AABB overlap, ideal circles or object names. The oblique machine proof shows
3D context and parallax but is too dark to visually certify every upper connection;
the saved geometry carries that particular bounded claim.

Keep the lower-wrap carryover separate. R01 measured positive finite-polygon gaps
at 32 of 56 stations, maximum 0.415 mm, despite valid ideal-circle overlap math.
Those surfaces were unchanged in R02 and no new sweep was performed. No visible
gap was identified at delivered R01 hero/proof resolution, so it remains optional
numerical cleanup rather than the leading painting priority. Never call it fixed
because the upper hubs now pass.

[Original upper-rim probe](../../qa/v0.1.5/evidence/recovery_run01/review/factory_upper_pulley_probe_r01.json)

## 6. Freeze selections and name controls accurately

Preserve both the early checkpoint and the selected variant. R02’s selected street
corrects the early dry/gray road; the factory uses a broader chosen floor atlas
after a first atlas suggested parallel boards; the selected mine uses a balanced
continuous density field. An early preview is useful failure evidence, not the
final result. Bind actual final images to the selected saved scene hash before
starting the next iteration.

Selected R02 scene identities:

- Street: 9d4a246fb1f4a4faa189cd6786f6f789dc39ee9bdfdf5b3da8c62c81e85837c7
- Factory: 32a63e2ee4c1b91a521c4efcbb2b6f6375d11e1185a548cfa5cf84f40a089583
- Mine: 7c10caea51575f92c2bdb4cc931172109753d719c90b8693e48a791a211cc40d

The factory light-control pair holds selected R02 geometry/materials/camera fixed,
then restores 37 named R01 light-property sets in memory for the second image.
World/fog are unchanged. It attributes the lighting contribution; it is not a
historical R01 scene rerender. The combined factory hero cannot attribute every
improvement to floor pigment alone.

The street alternate diagnostic changes the camera and adds a recorded cool
light; those overrides are not saved into the selected scene. The R01/R02 street
comparison also includes changed rain-film outlines and wetness, so it is not a
whole-frame single-variable shader experiment. Preserve these qualifications.

The mine smoke has a true closed domain, nonemissive volume-only output and a
parented object coordinate frame. Three recorded common-rigid-transform witnesses
remain stable. Analytic spine/density bounds are construction checks, distinct
from optical appearance. Actual hero/off-axis evidence supports source-to-tail
continuity; mixed edge and density design remains an art target. Do not keep
repeating the superseded dotted-source/black-terminal complaint.

Generated worker concepts are design aids. Generated atlases are texture inputs.
Actual Blender images are scene evidence. Grayscale sheets and crops are labeled
analysis derivatives. Keep all four categories separate and retain every original
binding. No technical pass or selected delivery checkpoint grants user approval
or whole-image artistic acceptance.

[Light-control record](../../qa/v0.1.5/evidence/recovery_run02/industrial/qa/factory_R02_floor_light_control.json)

## 7. Recovery needs packed scenes and exact build dependencies

Before further iteration, retain a durable packed editable scene and the exact
executed source/QA dependencies. Record scene/source/image hashes and file sizes.
Keep selected filenames immutable and work on a separate named copy. A transient
workspace path, a preview image or an old source script alone is not sufficient
recovery material.

R02’s recorded editable backup contains three selected packed scenes, two source
ZIPs and actual previews. Its manifest binds a 116,725,484-byte ZIP, split into
seven parts, to exact SHA-256 identities. The recorded restoration test reports
actual helper execution, archive SHA-256 and ZIP CRC passing. The 0.1.5 work only
rechecked original byte identities and inspected source-archive members; it did
not rerun restoration or claim an independent Blender reopen.

For a recipient-facing split backup, preserve ordered names, sizes and hashes of
every part, plus a restoration helper and the reconstructed archive identity.
Validate path safety and CRC, test restoration into a separate destination, and
verify recipient access before declaring delivery complete. Transfer success,
restoration success, packed editability and clean rebuild success are separate
claims.

R02 source scripts are delta builds with documented R01 baseline dependencies and
original workspace paths. They are not a from-scratch generator of the historical
project. Packed selected scenes can be edited directly; rebuilding requires the
proper baselines/assets and a consistently relocated path setup. No complete
independent clean reconstruction replay was performed.

The add-on source bundle keeps 27 new exact report/manifest copies, source-package
member hashes and external image/scene/backup identities. It deliberately omits
large recovery scene/image archives. The inherited roof companion’s existing
packed asset is retained unchanged for its own portable dependency contract.

- [Backup manifest](../../qa/v0.1.5/evidence/recovery_run02/delivery/DELIVERY_MANIFEST.json)
- [Recorded restoration test](../../qa/v0.1.5/evidence/recovery_run02/delivery/RESTORATION_TEST.json)
- [Backup instructions and limits](../../qa/v0.1.5/evidence/recovery_run02/delivery/README_Painted_Environments_R02.txt)
- [Street source dependencies](../../qa/v0.1.5/evidence/recovery_run02/street/README.md)
- [Industrial source dependencies](../../qa/v0.1.5/evidence/recovery_run02/industrial/README_R02.md)

## What remains open

The whole-image painted target remains unfinished. The R02 reviews prioritize
light/shadow grouping, stone material identity, selected damp-road intervals,
near-worker form/paint integration and smoke-edge design, with the nearest mine
hill direction secondary. The foreground floor treatment and inherited topology
qualifications above remain explicit. Missing cart-rail support, all-pairs
collisions, arbitrary animation or unviewed contacts are not invented failures;
they remain untested scopes. R03 results must receive their own future evidence
cut and cannot retroactively alter these frozen reports.
