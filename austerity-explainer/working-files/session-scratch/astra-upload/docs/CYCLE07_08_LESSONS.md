# Cycle07/08 lessons: construction, painted groups and trustworthy evidence

0.1.4 is a **guidance/data review candidate**. It adds no automatic scene repair,
material constructor, geometry auditor, render queue or hardware-coupled control.
All nine new recipes are experimental manual workflows with explicit selection,
coordinates, evidence requirements and rejection conditions. No preset changes.

These are lessons from frozen cycle07/08 reports, not fresh production tests by
this release. Cycle08 has visible improvements but remains below the requested
painted reference language. The later cycle09 work is outside this evidence cut.
The exact report hashes are in `data/lessons.json`; report links below resolve in
the source bundle, not a stand-alone installed extension. Images and production
scenes are not bundled, and this release did not independently inspect their pixels.

## 1. Verify the complete geometry–material chain

Closed edges do not establish outward winding. Pass07 had 81 affected street
owners even though positive total shell volume looked reassuring. Test paired-edge
orientation and signed volume **per connected closed component**, alongside finite
coordinates, degeneracy and edge incidence. Pass08's builder reports 82 repaired
owners after also finding four inverted disconnected bricks. Its 8,991-component
census is broader than the independent review's two saved-object samples. Neither
scope certifies intersections, structural adequacy or arbitrary future parameters.

A material slot or preserved graph also does not establish the shader's inputs.
Traverse connected inputs of materials actually used by faces, including nested
groups. Verify exact attribute names, domain/type, count and finite values, plus
the UV layer actually read by the image node. Preserve coordinate meaning:

- Street `paint_rest_position` copies POINT `paint_coords`, which is local/rest
  data in this source. World coordinates would change those fine-mark semantics.
- Normalized structural sections need physical as-built paint coordinates and
  metric UVs after applying width/depth dimensions. Layer existence is not proof
  of physical mark scale or noncollapsed coordinates.
- Long grain, cut-end grain and rest position are distinct contracts. The 60 mine
  boards retained endgrain slots in pass07 but used long grain on every new face.
  Pass08's three independently sampled boards have two real opposite end faces,
  eight long-grain faces and noncollapsed cross-section UVs. Do not describe that
  sample as an independent check of all 60 boards.

BMesh may omit an all-zero built-in material-index layer. Compare face assignment
semantics separately from storage and preserve both if exact rebuild equality
requires both. Boolean cutters can also introduce empty material slots; inspect
cut-face assignment and unused slots explicitly.

At the cycle08 freeze, `C03 joined return boundary 1 31` still lacks `paint_tone`
and `paint_exposure`; `C03 joined return boundary cap 1 31` lacks `paint_wetness`.
They are inherited connected inputs, not new cycle08 regressions. The proposed
next-copy repair is precisely these FLOAT/POINT zero fields, preserving the current
missing-input fallback. It is not a blanket reset of authored scalar data, and
0.1.4 does not apply the repair.

Sources: [cycle07 technical review](../../qa/v0.1.4/evidence/cycle07_technical.md),
[cycle08 technical review](../../qa/v0.1.4/evidence/cycle08_technical.md),
[street lessons](../../qa/v0.1.4/evidence/cycle08_street_lessons.md),
[industrial lessons](../../qa/v0.1.4/evidence/cycle08_industrial_lessons.md).

## 2. Keep assembled controls honest

The pass07 mine's default tie/fishplate contact was valid. Its displayed minimum
section depth opened a 97 mm gap because fixed hardware did not follow the beam.
This is a failed non-default range, not evidence that the default assembly floated.

Cycle08 intentionally locks 35 mine and 175 factory assembled section owners to
their verified as-built sizes. The limit is named in the UI and enforced inside
the graph. Two representative saved owners retain identical evaluated output
under extreme injected width/depth values and restore exactly. The fixed-size
state is safer but is **not functioning hardware-coupled resizing**.

Keep the editable source profiles. Before exposing a useful live range, derive
fitting placement, joints and physical paint scale from the same dimensions, then
test effective output, endpoint contacts, representative combinations and exact
restore. Do not unlock a misleading slider merely to make a scene appear procedural.

Sources: [cycle08 saved probe](../../qa/v0.1.4/evidence/cycle08_probe.json),
[industrial evidence index](../../qa/v0.1.4/evidence/cycle08_industrial_index.md).

## 3. Challenge the verifier, including curves and image interpretation

Use a controlled change that must fail, followed by exact restoration. Pass07
demonstrated an omitted bevel-property comparison and an older street camera-lens
blind spot. Cycle08's street fresh-rebuild comparison still misses two witnesses:

- `mud_height.png`: `Non-Color` → `sRGB`, despite a linked texture output
- A garment curve point moved +0.125 m on local X, with changed evaluated geometry

Both mutations escaped that comparator and were restored without saving. These
are defects in the **verifier**, not evidence those changes exist in production.
The separate protected-state auditor already captures curves; reuse that coverage.

Capture the render-relevant built-in modifier and camera/light state, mesh arrays,
material indices and attributes, curve spline/point/handle/radius/tilt/closure/
resolution/bevel/extrude state, bindings and representative evaluated geometry.
For images retain color-space interpretation and alpha mode alongside exact bytes,
size, packing and qualified path rebases. Alpha-mode capture is a recommendation;
the cited negative witness changed color space, not alpha mode.

Canonicalize serialized types before comparing. Cycle08's first audit reported
22,965 apparent material-binding differences from JSON lists versus Python tuples.
That was a representation artifact. Retain and label superseded reports; do not
convert a faulty test into a scene defect or silently erase a genuine failure.

Sources: [exact independent witnesses](../../qa/v0.1.4/evidence/cycle08_probe.json),
[three next technical patches](../../qa/v0.1.4/evidence/cycle08_technical_patch.md).

## 4. Contact and clearance need the actual surface and route

Pass07's rear/side flashing lay below the actual evaluated roof surface. The
cycle08 builder fitted thin sheets to roof samples, separating flat bases from
upstands. Its 3,120 saved support probes and nine doorway-approach rays are finite
geometry evidence. The rear-oblique rendered contact proof was deferred.

Measure support across the relevant footprint, not only at a centerplane. The
example's 4 mm embed, 14 mm visible lap and 180 mm upstand are local authored
values, not defaults. Test facade opening separately from the route in front:
the distant street repair had to clear brick instances, underlying wall and cap.
These tests do not establish whole-scene walkability or all-pairs collision safety.

Source: [selected street report](../../qa/v0.1.4/evidence/cycle08_street_final.md),
qualified by the [independent review](../../qa/v0.1.4/evidence/cycle08_technical.md).

## 5. Painted grouping is a choice of values, shadows and edges

Keep the actual construction gains. Both reviews find inward street reveals,
substantial mine structure and legible factory work planes. The next style step
is not a blanket geometry rebuild or another layer of stochastic noise.

**Wall planes:** author a few broad, irregular warm/cool and light/dark regions
across several courses, with quiet interiors and mixed firm/lost boundaries.
Use an explicit stable assembly frame and pass it deliberately through instances.
Preserve local rest coordinates for fine pigment. Do not double-transform an
already world-space Position or substitute camera projection.

A coherent wall-plane diffuse-normal branch in quiet regions is an experimental
proposal. Retain native response around selected sills, reveals, arrises, lamps
and contacts. Changing diffuse normals does not remove actual geometric cast
shadows; the lighting may also need a deliberate hierarchy. Reject the branch
if wall units still dominate, recesses flatten, mortar disappears up close or
contact shadows lose coherence. No recipe here implements this branch.

**Wet ground:** correlate color, roughness, normal attenuation and real reflection
response. Prefer linked rut/runoff masses with matte interruptions and selected
crisp dry stones. Street candidate A's obvious oval gloss stamps remain rejected;
B's improved wet/dry organization is real but does not solve every cobble edge.
Do not turn the road uniformly matte or paint cyan reflections into emission.

**Mine:** retain quieter coherent iron and the newly visible hill facets. Add only
selective joint/runoff accents, a stronger connected wet path, irregular near-hill
slope planes and smoke lobes with unequal size/density and dissolving gaps. Uniform
noise, equal spheres or restored all-over iron streaks would miss the finding.

**Factory:** broad blue/ochre/brown floor pigment already existed. The key next
test is light and shadow over those fields: selected asymmetric near/middle work
zones, meaningful dark intervals and side-origin atmosphere. Preserve the dark
roof and glossy brass. More floor noise, global exposure changes or equal stronger
lights for every bay do not establish the intended organization.

**People and timber:** keep garment-local value planes and sparse existing seam/
cuff/collar accents; retain volume, poses and contacts. Keep quieter factory wood
planes and selectively board-directed wear. Neither family needs universal outlines.

Sources: [cycle07 art review](../../qa/v0.1.4/evidence/cycle07_art.md),
[cycle08 art review](../../qa/v0.1.4/evidence/cycle08_art.md),
[proposed next tests](../../qa/v0.1.4/evidence/cycle08_art_plan.md).

## 6. Stage the queue without inflating acceptance

Use cheap contract checks and bounded negative controls before expensive rendering.
Make a small attributable preview, select the useful candidate, then render the
same final hero and most informative detail. If a claim concerns mapping or
reflection stability, include an alternate camera before accepting that claim.
This is workflow guidance, not a measured performance promise or built-in scheduler.

Where the official-MCP workflow applies, cooperate with its existing CPU_RENDER
then BLENDER_MCP lock order and release each job's locks. 0.1.4 starts no Blender
process and acquires no render or MCP lock. Production builders are left undisturbed.

Cycle08 finished each hero and one facade/headgear/workstation diagnostic. Several
alternates, rear-contact and extra asset/worker details and exhaustive matrices
were deferred. Those missing outputs do not become delivered evidence because
scripts exist. Neutral asset lighting proves local readability, not production mood.

For each image claim retain scene/render hashes and runtime/camera/light settings.
Inspect thumbnail hierarchy, ordinary-size reading and native detail against the
original references. Separate genuine improvement, unchanged targets, regressions
and open limits. Technical passes, node labels or a requested defect count never
establish painted-style success; do not invent findings to meet a quota. An
authorized continuing art cycle ends at the user's stated stopping condition,
not an automatically computed score or an earlier critic's all-clear.

## Release verification boundary

Fresh 0.1.4 checks are Python/data/source and packaging checks only, documented in
[TEST_REPORT.md](TEST_REPORT.md). Five runtime modules are compared with the exact
0.1.3 ZIP, allowing only the declared release metadata substitutions. Companion
files, settings/presets, preview transactions and exclusions remain unchanged.

No fresh Blender registration/recovery/render, official extension CLI validation,
interactive installation, production scene test or user art acceptance is claimed.
Prior Blender 5.1.2 tests remain inherited, hash-bound 0.1.3 evidence. Root's fresh
independent review of this new guidance/package is still required before release.
