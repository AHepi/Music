# Current release: 0.2.0 runtime tools

This installation adds real terrain, scatter, plank and material-specific operators in the Astra Paint sidebar. Start with [Runtime 0.2.0](RUNTIME_020.md), [migration and limits](MIGRATION_020.md), and [qualification](QUALIFICATION_020.md). The earlier sections below are preserved historical guidance; their “guidance only / no new operator” statements apply to those older release checkpoints.

# 0.1.9 architecture guidance boundary

Read [R11/R12 lessons](RECOVERY_R11_R12_LESSONS.md) for accepted scoped architecture
and manual verification practices. The 83 lessons/recipes are data; no new runtime
operator or live GN architecture system is installed. The actual accepted layout
is verified, but its helper retains numeric cutoffs and is not universally exact.
No fresh Blender, scene, image or installation qualification is added.

Earlier guidance retains its original chronology and follows unchanged.

# Current 0.1.8 guidance addendum

Guidance-only candidate, pending independent package review. Runtime changes from accepted 0.1.7 are exactly four version/UI metadata substitutions, with no new scene mutation, compiler, generator or operator. See [R09/R10 lessons](RECOVERY_R09_R10_LESSONS.md) and [current test scope](../../qa/v0.1.8/TEST_REPORT.md).

The final frozen source findings supersede only their named historical pending gates. Stronger factory hero readability remains unmet; S1 remains unselected; R11 generated studies are UNIMPLEMENTED concepts and its active architecture is excluded. All earlier text below is retained verbatim as historical provenance, including old cutoffs and test qualifications. No new Blender, image-pixel/EXR, install, undo, restore or platform test is claimed.

# Astra Painted Workbench 0.1.6

Guidance-only candidate; independent release review pending. Runtime behavior and preview eligibility are unchanged apart from version metadata.

Read [the R03/R04 guide](RECOVERY_R03_R04_LESSONS.md) for reference-scale design, spherical-sky diagnostics, exact owner selection, outward winding, perimeter terrain contact, multi-scale wear and accurate branch attribution. The registry now holds 44 manual/scoped lessons and 44 recipes. No new scene-edit operator is added.

R03 repaired the foreground floor coverage; R04 repaired five gable windings, terrain burial and four unintended visibility states. Final street v03/mine v02/factory B2 are bounded technical baselines, not artistic completion. R05 plans are prospective, with no outcome claimed. Earlier evidence cuts below are historical and remain unchanged in their original accepted archive.

# Historical 0.1.5 usage and recovery notes

A small, modular Blender 5.1 tool for developing painted environments. It carries
reusable controls, explicit safety boundaries and lessons from actual scene work.
Every non-neutral built-in study remains experimental. Version 0.1.5 changes
guidance/data and release metadata only; the 0.1.1 transaction safeguards remain.

## Recovery R01/R02 guidance in this candidate

Read [the recovery guide](RECOVERY_R01_R02_LESSONS.md) for flat pigment mapping,
stone/wood identity, protected character anchors, inherited topology, explicit
floor coverage, real hub/spoke connections and durable frozen backups. These seven
manual recipes do not add runtime behavior. R03 is outside the verified evidence
cut. The whole-image target, Mesh_00139 coverage correction and inherited head/palm
split-face qualification remain open at the R02 freeze. Original scene/image
identities and reviewer scope must not be replaced by generated concepts.

## Start here

1. Save a separate working copy of your scene. Use Cycles for material previews.
2. In Object Mode select a small representative group. Open **3D View → Sidebar
   → Astra Paint**. The default settings are inert. No assets change on install,
   file load, preset load or slider movement.
3. Load a family or lighting study. Choose the material family explicitly and
   verify local-axis mark frequencies. Active material slot only is the default.
4. Click **Inspect Selection**. Open the named Blender Text for eligible actions
   and reasons that unsupported targets will be left alone.
5. Acknowledge experimental status, then **Start Reversible Preview**. Only
   selected eligible mesh/light data gets private copies. Existing object
   transforms, world, camera and compositor are not modified. There is no
   automatic file save.
6. Inspect actual Cycles pixels at hero and native near scales. Changing sliders
   during an active preview does not update it. Revert, adjust, then preview again.
7. **Revert Preview** restores tracked original data even if selection changed.
   **Keep Preview** keeps the edits and releases the special revert snapshot.
   Standard Blender Undo applies to the operators; it is not a substitute for a
   saved baseline. Keeping an edit is not artistic acceptance.

Do not edit preview data, slots or modifiers through other tools before deciding.
Revert discards changes within the private preview mesh/material/light copies,
including manual edits made to those copies. The guard is not a general edit-history
detector. Keep Preview preserves such work if you want to retain it.
Before restoring any target, Revert checks every current preview binding and every
original destination material-slot layout/identity, including originals shared with
unselected users. Conflicts preserve all targets and transaction state. Restore the
conflicting binding/layout or Keep to preserve outside edits. Deleted targets are
not recreated. Original shared mesh/material interiors are not immutable backups: if
you edit them elsewhere, those edits remain in the original data.

The tracked bevel has a conservative saved-state guard (name, stack position, UID,
scalar/array settings and profile points). Any difference blocks Revert, including
edits to the original tracked bevel. Blender can reuse a removed modifier UID, so
UID/name alone are never treated as proof. An exact clone of all recorded fields
can remain indistinguishable; this is not an edit-history guarantee. Keep or Revert
before deleting/rebuilding modifiers. Edits to unrelated pre-existing modifiers
are not generally audited or reverted. UI expansion/active-modifier state is ignored.

Preview state is saved in the .blend. Re-enable this extension before recovering
an active saved preview using snapshot schema 1.1 (runtime lineage from add-on 0.1.1).
0.1.5 verifies exact uploaded 0.1.4 metadata-only equivalence and the inherited
0.1.3 runtime baseline; it does not rerun Blender recovery.
Version 0.1.0 snapshots lack the new
destination/state evidence and fail closed on Revert; they are not auto-migrated.
Resolve old previews on a saved test copy before upgrading, or use Keep and a saved
baseline. Disabling the extension restores an uncomplicated active
preview. If outside edits conflict, it leaves data and snapshots for recovery on
re-enable instead of guessing which edits to destroy. See the QA report for the
actual tested recovery cases. Do not purge orphan data while relying on a preview.

## Separate the five jobs

**Pigment authoring:** Broad, material-specific color/value passages, wear and
directional marks belong to the asset. This release does not fabricate painted
texture assets or wrap scene-specific floor/cloth/sky mappings. Material response
cannot create missing pigment structure.

**Surface response:** The selected direct opaque Principled shader is retained
and mixed with an opt-in Cycles diffuse/toon response. Its connected base color
and authored normal remain sources. A bounded rest-local perturbation can be
added to the response normal. This is intentionally smaller than the production
pipeline: no registered shader groups, compositor, coherent diffuse reconstruction,
scene AOVs, material-wide roughness repair or beauty-image posterization.

**Lighting:** Selected light energy and tint can be changed on private copies.
The studies are an A/B aid, not accepted street/factory/mine palettes. Lighting
affects other objects through transport even though only selected light data is
edited. World, volume, atmosphere, camera and display transform are separate.

**Atmosphere:** Design depth and edge loss for the actual scene. A generic smoke
topology, world-XY factory wear mask, world-direction painted sky and pose-bound
cloth field are different coordinate contracts. None is applied by this release.
The data-only atmosphere recipe is a proposed artist workflow, not implemented
volume construction or an accepted look.

**Composition:** Use a meaningful fixed camera first, then meaningful alternate
views. Do not improve one proof by hiding its defect. A camera fixture correction
needs a stated reason, a new identity and retention of the failed picture.

## Whole-image comparison comes first

Compare actual renders with the original supplied reference, not only a generated
concept or a numerical gate. At thumbnail and native detail scales ask:

- Are the large light/dark groups and focal illumination comparable?
- Are broad warm/cool relationships and shadow colors integrated?
- Does foreground/midground/background contrast recede coherently? Where are
  edges lost, softened or retained by atmosphere?
- Do wood, cloth, plaster, stone, ceramics and metal have different mark scale,
  orientation, hierarchy and highlight behavior?
- Do figures and setting belong to the same shape, material and lighting language?
- Are objects grounded on visible physical supports, joints coherent and routes
  clear in the declared inspected views?

The pass02b history showed why this is necessary: local floor/cloud/puddle
improvements still coexisted with wrong whole-image light/depth relationships,
and directional cloth noise produced concentric wrapping bands. Fresh pass03 art
review subsequently closed the finite factory depth, mine dusk and cloth-band
findings. Street’s broad cool wet grouping passed; its lamp-local transition
remained open at the cited review. Preserve those closures instead of turning
cleaner edges, quiet cloth or different ground detail into endless new work.
These are source-example verdicts, not acceptance of the add-on’s study values.

Declare the user’s whole-image goal, current criterion, affected views, preserved
wins, allowed test and stop condition before editing. A user rejection supersedes
prior critic artistic closure and can show that the criterion itself was too narrow.
Reassess the whole image instead of using the ledger to dismiss that feedback.
Close adequate satisfied criteria and deliver for user review; a critic pass is
not user approval. Technical strict failures retain their raw labels;
a separate nonblocking still-image disposition does not erase them.

First isolate lighting/atmosphere in a fixed-camera A/B while holding geometry and
pigment stable. Only make a conditional pigment change if the mismatch remains.
A camera/light robustness matrix with the same world and sky is useful stability
evidence; it is not a general art-direction lighting comparison. Checklist boxes
record that someone inspected a question. They never produce a score or acceptance.

## Material and geometry boundaries

- Only direct opaque Principled surfaces through optional reroutes are supported.
  Mixed/grouped shaders, transmission, linked alpha, active emission, volume,
  displacement, animated graphs and already-styled materials are preserved.
- Families are explicit. Water, glass, foliage, skin and hair are not auto-styled.
  Fabric studies are experimental response only; no production cloth flow is used.
- Rest coordinates are stored on private mesh copies, in metres using world-axis
  scale magnitudes at bind. Translation/rotation follow the asset. Later scale or
  deformation changes require a new validated bind. Shear/singular transforms,
  shape keys, armatures, simulations and geometry-node generation are excluded.
  Existing modifiers are limited to Bevel, Subdivision, Triangulate, Weighted Normal
  and Edge Split, including disabled modifiers conservatively. Object/parent
  animation, drivers and constraints are excluded. Read-only geometry diagnostics
  may still inspect rejected deforming meshes. This is not a universal transform
  or animation invariance claim.
- Known collection-instance sources are rejected across all loaded scenes, including
  nested collections, as are vertex/face-instanced children and particle instance
  references. Nothing is automatically realized. Selected-only means object-ID
  edits: lighting/transport and indirect modifier dependencies can affect other
  pixels. Arbitrary Geometry Nodes/dependency references are not exhaustively found.
- The optional edge bevel is an unapplied, angle-limited modifier. It requires
  uniform world scale, is bounded to 10% of the smallest base-mesh extent and clamps
  overlap. It does not author material-specific chips, preserve every contact or
  certify geometry. Review silhouettes, exposure and physical supports afterward.
- Do not shrink every beam to treat one black joint. In tested scenes, exposed
  same-facing coplanar faces caused rectangular black patches. A bounded coherent
  inset removed a diagnosed patch while separately tested supports remained valid.
  Hidden structural intersections can be intentional.
- Targeted joint tests certify only their stated rays and pairs. A later alternate
  view exposed an inherited shoji rail/stile coplanar patch beyond four previously
  passing post/beam/step witnesses. Later bounded proofs separated rail/stile
  exposed-face competition from overlapping fixed/parked paper. Those mechanisms
  needed different coherent local repairs and separate support/gap checks. Seven
  named passing rays still do not establish whole-scene coplanar clearance.
- Stone/foliage treatments need mass hierarchy. Blanket vertex jitter, repeated
  chipped blocks, oversized foliage triangles and uniform granular noise are not
  transferable defaults. Proposed forms remain separate from accepted code behavior.
- An authored image mask can still look like a repeated polygon-cell stamp.
  Judge actual mark shape, edge loss, physical scale and repetition in representative
  views. Avoid treating a node-type ban, a hand-authored label or a tiny blur radius
  as evidence that a surface has acquired convincing broad paint structure.

## Geometry evidence is scoped

**Audit Evaluated Selection** synchronizes the view layer before reading evaluated
world vertices and triangles. Reading copied-object matrices too early previously
produced a false obstacle layout; an actual saved-output audit exposed overlap
that source-only replay and covered camera rays missed.

The report supplies finite-coordinate/degeneracy observations, geometry fingerprints,
bounds, visibility and AABB overlap candidates. An AABB candidate is not a real
intersection test or defect. Instances are not flattened. Viewport and render
modifier states may differ. No watertightness, collision or structure certificate
is produced.

**Probe Active Support** uses the explicitly active selected visible mesh as the
physical support; other selected meshes are targets. It casts downward from outside
the support to at most 128 evaluated target vertices within 3 mm of the target's
lowest world-Z value. Raw misses and signed gaps are retained, with no guessed
ground height. This is a finite bottom-band witness, not a full sole, slope,
overhang, penetration or route-clearance test. A negative gap is an observation,
not automatic rejection of intentional embedment.

Use the custom property astra_role = surface_art for objects that are pigment-only
overlays; those are excluded as supports. The transport_envelope and volume_domain
roles and mesh envelopes whose assigned materials are all volume-only are also
excluded. A transport domain stays visible to rendering; exclusion from support
tests is not an instruction to delete or hide it. Render-hidden or viewport-hidden
supports are rejected. The tool cannot infer that an untagged visible plane is nonphysical.
Changing visibility can invalidate contact attribution even if mesh positions are
unchanged. Replay old rays against the actual remaining physical support.

Support and walking clearance are separate. A bridge can retain valid bearers and
still have bank stones obstructing its deck. Small numerical failures must stay
failed in the raw evidence, with any nonblocking still-image disposition recorded
separately; do not quietly relax tolerances or demand irrelevant perfection.

## Evidence and LLM handoff

Config to Text exports versioned JSON. Load Config Text validates it as data only;
unknown keys, unsupported versions, nonfinite numbers and out-of-range controls
are rejected, as are duplicate keys and text over 64 KiB. Integral JSON segment
values such as 2, 2.0 and 2e0 normalize to integer 2; fractional/bool values do not. During a preview,
the export contains its frozen applied configuration. Nothing in a recipe executes Python, reads external accounts or
automatically selects production assets. No network or external dependencies are
used by the extension.

Bundled data/config.schema.json defines settings. data/recipe.schema.json and
data/recipes.json describe selection contracts, constraints, implemented versus
proposed steps, required evidence and stopping conditions. data/presets.json keeps
parameter provenance and art acceptance separate. data/reference_checklist.json
holds the fuller human rubric and finite closure policy. data/lessons.json and
lessons.schema.json bind source evidence, validation scope, example art disposition,
coordinate ownership and unsupported cases. Scene acceptance never promotes a
built-in preset. data/llm_contract.json maps each workflow action to
the actual operator ID, input, output and safety scope through explicit action-token
mappings. Load/configure first, inspect that exact configuration and selection,
obtain human acknowledgment, then preview. Reinspect after settings/selection changes.
Visual rendering/review remain manual; the record operator only saves observations. It is an integration guide,
not authorization to execute a task.

For review, bind the exact source/config, saved scene and rendered PNG/EXR hashes.
Record actual camera fields, light sizes/shapes/colors/energies, engine, frame,
sample count, seed and view transform. Runtime reports capture supported camera,
light and render fields but not every world/volume node or renderer option. They
are not a replacement for the actual saved scene hash. Distinguish file-byte
identity, decoded-pixel identity, same-file reload and independent-build identity.
Use native, unresampled crops and retain the original whole image. Strict
independent-build failures cannot be erased by successful same-file reloads.

## Acceptance and limits

The unchanged runtime has inherited Blender 5.1.2 synthetic-fixture evidence.
Fresh 0.1.4 tests are Python/data and packaging only; no Blender process or
production scene is loaded by this update. Read TEST_REPORT.md for exact stages.
Code behavior, measured transport, evidence coverage and artistic acceptance are
separate claims. No built-in study is a finished reference match; no whole-scene
lighting, arbitrary shader graph, animation, large-scene performance or cross-version
guarantee is offered. The useful default is neutral and reversible.


## Dated developing lessons

See PASS03_LESSONS.md for the compact decision guide and the versioned lessons
registry for exact dated provenance. Test renderer behavior with actual outputs: a
stored light field can be inert in a particular Cycles path. Keep reflected-source
coverage, participating-air scale, visible sky, diffuse fill and artistic world-depth
palette ownership explicit. New recipes are manual; no atmosphere, ray-visibility,
foliage or joint-repair operation is installed.

## Latest user feedback: Japanese acceptance reopened

At 2026-10-17 14:26:44 UTC the user rejected Japanese v13 completion and reference
closeness. Its previous critic acceptance is superseded. Local plaster/pine/joint
observations and measured support/rebuild facts remain scoped evidence, but they
do not establish a finished or reference-matched scene. The fresh task is holistic
style reassessment, including whether the prior restricted issue ledger was adequate.

The user also requires Blender MCP access and awareness of procedural generation
and Geometry Nodes in the scene-authoring/review workflow. Verify actual tool
availability and structured outcomes; use those authoring methods where appropriate
with evaluated and rendered evidence. This data-only release adds no MCP execution
or Geometry Nodes mutation adapter; its existing preview exclusions remain intact.

## Image-led components in 0.1.3

Read IMAGE_LED_LESSONS.md for the current Japanese limitations and tested water,
barrel and mine workflows. A separate experimental Roof Course Lab library is
manual-append data/source only; this selection preview still rejects Geometry
Nodes. No production system, automatic scene orchestration or new mutation
operator is added. Generated pigment assets retain mapping/provenance.


## Cycle07/08 guidance in 0.1.4

Read [CYCLE07_08_LESSONS.md](CYCLE07_08_LESSONS.md) for component winding,
connected face-used shader contracts, physical UV/endgrain, fixed-size assembled
controls, curve/image-interpretation comparator coverage, actual support/approach
tests and experimental painted value/shadow/edge studies. The staged render plan
is manual guidance only. No auditor, constructor or render scheduler is installed.

Cycle08 remains an unfinished artistic iteration. Three inherited street scalar
inputs and two street fresh-rebuild verifier blind spots were open at this frozen
evidence cut. New cycle09 work is outside that snapshot. Do not use an old report
as a claim that later work failed, passed or reached final visual acceptance.


## 0.1.7: R05–R07 and the explicit uneven-facet brief

Read [the dated R05–R07 guide](RECOVERY_R05_R07_LESSONS.md). The twelve new lessons are manual data only. R05 remains native baseline; R06 candidates are rejected; R07 street is optional static presentation with known scalloped contours. The generated factory target supplies a project design constraint, not verified Blender geometry or a completed R08 outcome.
