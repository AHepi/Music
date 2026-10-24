# R11/R12: stable architecture cells, supported routes and honest proof

0.1.9 guidance-only candidate, pending independent package review. Evidence cutoff is the sealed R12 delivery at 2026-10-18 14:15 UTC. This package did not open Blender, render, inspect new image pixels, execute scene source or install the addon. All scene findings are attributed to frozen evidence.

C3 is an accepted bounded functional checkpoint with a real late diagonal brick-seam defect. A4b repairs that pilot and adds only Terrace_1_7 and Terrace_1_5 ground-front variants. R13 and later provisional work are excluded. Older lessons retain their original cutoff and statements, including the earlier R11-unimplemented status. This later guide adds chronology rather than rewriting history.

Complete positive coverage is a layout-specific verification requirement. A4b’s independently checked 322-cell result does not make its floating-predicate helper universally exact for arbitrary new apertures. Generated studies guide form; actual measured geometry and actual images govern.

The linked source evidence is present in the source archive only. The install contains guidance, not a new scene compiler, live Geometry Nodes system or automatic recipe executor. Inert source files retain scene-specific dependencies and are never invoked by the addon.

## 1. Assign variation once to each original logical brick

Stable logical-cell identity and independent random channels prevent aperture partitioning from changing one brick into several inconsistent surfaces.

**Observed scope:** C3 exposed a 2.047 mm intra-brick depth witness. A4b verifies stable row/column IDs, width/depth channels and module/order independence for the two actual variants.

- Allocate one depth per original brick before its fragment loop. C3 randomized fragment depths independently and beveled artificial partitions, creating real diagonal seams despite closed positive solids.
- Use persistent module/row/column keys and independent width/depth channels. Do not consume extra depth samples because one aperture produces more fragments.
- Retain cell records even when subtraction leaves no material. Compare IDs, bounds and depths under aperture changes, reversed opening order and reversed module execution.
- A4b has ten tested aperture/order cases and 200 exact no-intersection probes. These cover its actual two-module construction, not arbitrary new grids or topology.
- The repaired pilot maps 193 original cap fragments to 126 cells; select one original depth inside each cell envelope without claiming all former fragment depths remain unchanged.

**Ownership/coordinate contract:** Original logical brick identified by module, row and column, before aperture subtraction; Metric module-local planar cell and its single front/back depths; Keep cell ID and random channels stable through clipping, aperture order, empty-cell outcomes and module traversal; preserve between-brick variation.

**Not established:** No universal random-field or arbitrary-aperture determinism guarantee; clipping tests do not prove visual acceptance by themselves.

**Sources:** [r11_c3_final](../../qa/v0.1.9/evidence/r11_c3_final/C3_FINAL_REVIEW.md), [r11_c3_seam_addendum](../../qa/v0.1.9/evidence/r11_c3_seam_addendum/C3_frontal_line_addendum.md), [r11_c3_seam_measurements](../../qa/v0.1.9/evidence/r11_c3_seam_measurements/C3_frontal_line_addendum.json), [r11_c3_frozen_builder](../../qa/v0.1.9/evidence/r11_c3_frozen_builder/build_R11.py), [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_determinism](../../qa/v0.1.9/evidence/r12_a4b_determinism/A4b_cell_determinism.json), [r12_a4b_builder_source](../../qa/v0.1.9/evidence/r12_a4b_builder_source/build_R12.py)

## 2. Reunite planar cell fragments before adding depth

Subtract apertures in the cell plane, cancel artificial internal boundaries, and extrude only the intended material union.

**Observed scope:** A4b repairs the original pilot and verifies true-boundary-only bevels on its two new ground-front modules; each new mortar shell is one solid with two apertures.

- First establish actual overlap. C3 extended clipping planes partitioned a wholly nonintersecting rectangle; unchanged total area did not prevent false seams.
- Split shared collinear edges at partition vertices and cancel oppositely oriented internal edges within the same logical cell before extrusion. Never fuse neighboring bricks or mortar gaps.
- Give depth-return faces only to true union boundaries. Simple positive outer loops are suitable only for hole-free cells; cells with interior holes need an explicit holed-cap construction rather than silently filled ngons.
- Inspect actual evaluated bevel faces and source-bound neutral images. A closed mesh with positive volume is not evidence that artificial internal bevels are absent.
- The accepted shell retains coplanar cap partitions with controlled cleanup; this is distinct from indiscriminate 3D vertex dissolve. Recheck shell apertures, connectedness and retained upper/side components.

**Ownership/coordinate contract:** One original brick cell or explicitly owned wall-shell cell; never adjacent mortar/brick owners; 2D local material union plus front/back depth interval; Preserve no-intersection cells intact and retain real brick, aperture and shell boundaries.

**Not established:** No robust-exact Boolean kernel claim. Remaining floating predicates and layout-dependent degeneracies require new checks for changed apertures.

**Sources:** [r11_c3_seam_addendum](../../qa/v0.1.9/evidence/r11_c3_seam_addendum/C3_frontal_line_addendum.md), [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_technical](../../qa/v0.1.9/evidence/r12_a4b_technical/A4b_TECHNICAL_REVIEW.md), [r12_a4b_masonry](../../qa/v0.1.9/evidence/r12_a4b_masonry/A4b_complete_aperture_cells_independent_variant_masonry.json), [r12_a4b_shells](../../qa/v0.1.9/evidence/r12_a4b_shells/A4b_complete_aperture_cells_independent_shell_apertures.json), [r12_a4b_planar_source](../../qa/v0.1.9/evidence/r12_a4b_planar_source/planar_union.py)

## 3. Check complete material coverage, including exposed tiny corners

Verify the complete intended material set for each actual layout; a small positive region is not disposable merely because it is small.

**Observed scope:** A4b restores A4a’s connected 0.638679663 mm² exposed corner and passes independent complete-set comparison for 322 actual cells, including 63 empty cells.

- Do not discard aperture subtraction parts by a visual-size heuristic. The omitted A4a triangle was a connected exposed brick corner with mortar about 59 mm behind it, not an irrelevant detached sliver.
- Compare both area and symmetric difference against the complete unfiltered material set, including empty cells. Equal total area can conceal a relocated missing region.
- The 322-cell A4b specification comparison has maximum symmetric difference 1.96e-16 m². Inspect the saved front/back/side faces and actual loop triangles too: valid ngon boundaries alone do not establish filled coverage.
- A4b removes the explicit 0.00002 m² pre-union filter, but inherited clip2 still requires area greater than 1e-9, uses 1e-9 signed tests and 1e-8 distance cleanup; clean2 uses a 1e-10 collinearity cross threshold. Planar coalescence defaults to 1e-9 and its before/after area guard is 1e-8. These numeric predicates remain and must be disclosed.
- Full positive coverage is a required layout-specific verification target, not a universal guarantee of the accepted helper. Test near-threshold, tangency, coincident-edge and changed-aperture cases against an independent set oracle before reuse.
- The restored subpixel feature is established by saved-cap and actual tessellation evidence. Do not claim its entire tiny shape is visually resolved in the proof image.

**Ownership/coordinate contract:** Complete pre-filter rectangle-minus-aperture specification and actual saved cell caps/sides; Metric local plane; exact-rational comparison of the declared numeric coordinates, then float32 saved geometry; Recompute coverage and degeneracy checks for each changed layout; disclose all area, distance and collinearity predicates.

**Not established:** No arbitrary-aperture preservation of every positive region; no exact-arithmetic implementation claim, zero-tolerance universal proof or visual resolution claim for subpixel corners.

**Sources:** [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_technical](../../qa/v0.1.9/evidence/r12_a4b_technical/A4b_TECHNICAL_REVIEW.md), [r12_a4b_coverage](../../qa/v0.1.9/evidence/r12_a4b_coverage/verify_positive_cell_area_A4b_complete_aperture_cells_build.json), [r12_a4b_saved_caps](../../qa/v0.1.9/evidence/r12_a4b_saved_caps/verify_positive_cell_area_A4b_saved_sharp_caps.json), [r12_a4b_tessellation](../../qa/v0.1.9/evidence/r12_a4b_tessellation/verify_positive_cell_area_A4b_actual_tessellation.json), [r12_a4b_source_delta](../../qa/v0.1.9/evidence/r12_a4b_source_delta/A4b_independent_source_delta.json), [r12_a4b_geometry_source](../../qa/v0.1.9/evidence/r12_a4b_geometry_source/r11_geometry.py), [r12_a4b_planar_source](../../qa/v0.1.9/evidence/r12_a4b_planar_source/planar_union.py)

## 4. Use an explicit minimum-feature policy for genuine boundaries

A bevel must respect true construction boundaries and feature size; deliberate sharp treatment is safer than deleting material or allowing collapse.

**Observed scope:** A4b applies the declared 8.4 mm true-edge trigger against an inherited 4 mm bevel; three broad T5 bricks and two narrow T7 strips remain intentionally sharp.

- Measure real perimeter/aperture edges after internal partitions are canceled. Artificial cut edges must not trigger a bevel or a minimum-feature policy.
- Document whether the policy keeps a whole cell sharp, changes the intended bevel, or rejects the construction. Do not silently erase a positive feature or globally round the design.
- In A4b, the 8.4 mm trigger preserves whole cells sharp to avoid inherited 4 mm bevel collapse. T5 cells are approximately 390×197, 420×197 and 415×197 mm, triggered by small true edges; they are not tiny fragments. T7 has two narrow strips.
- Keep raw-face winding, closed incidence, positive volume, corner fields and effective material exact when partitioning companions. Confirm actual tessellation, not just an owner label.
- Require real close-view acceptance for broad sharp cells. The disclosed A4b choice is visually accepted in its actual views; it is not a general style default.

**Ownership/coordinate contract:** Whole logical brick with any genuine minimum edge below the authored threshold; Actual metric true-boundary edge lengths after planar outline construction; Retain coordinates, fields and material ownership when separating sharp companions; verify raw/evaluated geometry and appearance.

**Not established:** No universal 8.4 mm threshold or automatic bevel safety on different scales, corners, modifiers or apertures.

**Sources:** [r11_c3_final](../../qa/v0.1.9/evidence/r11_c3_final/C3_FINAL_REVIEW.md), [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_summary](../../qa/v0.1.9/evidence/r12_a4b_summary/A4b_EVIDENCE_SUMMARY.json), [r12_a4b_masonry](../../qa/v0.1.9/evidence/r12_a4b_masonry/A4b_complete_aperture_cells_independent_variant_masonry.json), [r12_a4b_tessellation](../../qa/v0.1.9/evidence/r12_a4b_tessellation/verify_positive_cell_area_A4b_actual_tessellation.json), [r12_a4b_builder_source](../../qa/v0.1.9/evidence/r12_a4b_builder_source/build_R12.py)

## 5. Preserve planar caps instead of dissolving 3D construction indiscriminately

Simplify intended planar boundaries before extrusion and separately check cap planarity; closed topology and positive volume can coexist with warped faces.

**Observed scope:** Rejected A3e had 60 nonplanar faces and up to 4 mm envelope growth. A4b’s 6,377 new saved polygons pass a 1 µm plane threshold.

- Do not use generic post-extrusion vertex dissolve to repair fragment seams. It can merge cap and return boundaries into warped ngons while leaving a closed positive solid.
- Simplify the true 2D outline before extrusion and retain explicit front, back and depth faces. Disclose remaining numeric cleanup thresholds and reject unsupported interior-hole topology.
- Check each saved polygon with at least four corners against an independent plane test, then check loop triangles, winding, incidence, component volume and source-envelope containment.
- A4b’s maximum observed plane deviation is about 0.042002 µm at the 1 µm test threshold. Those measurements certify the named new geometry only, not every inherited mesh.
- Controlled coplanar shell dissolve and 1e-7 duplicate/degenerate cleanup remain in the source. They are confined to new owners and checked afterward; no blanket prohibition or guarantee applies to every dissolve operation.

**Ownership/coordinate contract:** Newly authored cells and explicitly owned shell cleanup; protected source owners remain untouched; Local planar outline, front/back cap planes and depth return planes; validate saved world/local geometry consistently; Run checks after the final conversion and cleanup, not only before them.

**Not established:** No blanket inherited watertightness or arbitrary-cleanup safety; numerical nonplanarity is not automatically a visible hole.

**Sources:** [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_technical](../../qa/v0.1.9/evidence/r12_a4b_technical/A4b_TECHNICAL_REVIEW.md), [r12_a4b_planarity](../../qa/v0.1.9/evidence/r12_a4b_planarity/A4b_complete_aperture_cells_independent_face_planarity.json), [r12_architecture_ledger](../../qa/v0.1.9/evidence/r12_architecture_ledger/REVIEW_LEDGER.md), [r12_a4b_builder_source](../../qa/v0.1.9/evidence/r12_a4b_builder_source/build_R12.py), [r12_a4b_masonry_source](../../qa/v0.1.9/evidence/r12_a4b_masonry_source/local_masonry.py)

## 6. Audit actual saved geometry and effective material ownership

Inspect the saved/reopened object and its effective material slots; passing build assertions or mesh-data slots alone do not establish the delivered appearance or preservation.

**Observed scope:** A4b independently checks 63 changed originals, 14,198 exact originals and 106 new owners, plus a separate exact A2c binding for all 178 pilot-related saved owners.

- Read slot.material and its link mode. A source OBJECT override can differ from ob.data.materials; newly created owners must receive the actual effective material and intended link mode.
- R12 retained a real wrong-link-mode failure before correction. The frozen new_owned_masonry source explicitly assigns OBJECT and the effective inherited material; no new plugin operator is added.
- Check exact oriented retained faces and material/smoothing/paint/UV fields, transforms and modifiers. Index renumbering is not inherently a loss; comparisons need a stated semantic representation.
- Reopen the selected saved scene independently. An allowed-change set merely permits differences; separately bind protected gains such as the 178 pilot-related owners to their accepted checkpoint.
- Classify comparison scope honestly: R11 held global shader graphs and lighting while intentionally assigning existing dark timber to new joinery. It was not a strictly material-binding-invariant geometry-only test.

**Ownership/coordinate contract:** Declared changed/protected objects, mesh data, object material slots, nested material graphs and face/corner fields; Saved object transforms and local raw geometry; evaluated geometry and bindings checked separately; Copy effective OBJECT-linked materials when creating replacement objects, and preserve retained components/fields before and after final save.

**Not established:** No all-owner clean-mesh claim, no guarantee from build assertions alone, and no claim every object material assignment remains unchanged.

**Sources:** [r11_c3_final](../../qa/v0.1.9/evidence/r11_c3_final/C3_FINAL_REVIEW.md), [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_scope](../../qa/v0.1.9/evidence/r12_a4b_scope/A4b_complete_aperture_cells_independent_scope_topology.json), [r12_a4b_pilot](../../qa/v0.1.9/evidence/r12_a4b_pilot/A4b_complete_aperture_cells_independent_pilot_transfer.json), [r12_a4b_masonry](../../qa/v0.1.9/evidence/r12_a4b_masonry/A4b_complete_aperture_cells_independent_variant_masonry.json), [r12_architecture_ledger](../../qa/v0.1.9/evidence/r12_architecture_ledger/REVIEW_LEDGER.md), [r12_a4b_masonry_source](../../qa/v0.1.9/evidence/r12_a4b_masonry_source/local_masonry.py)

## 7. Measure a fully supported body-height route to a real landing

A usable route is the connected intersection of actual support and relevant body-height clearance, ending at a genuine approach or landing.

**Observed scope:** C3/R12 main route has 694 sampled sections, minimum 1.382960024 m, none below the authored 1.35 m target and 15 below 1.50 m; terminal has distinct envelope assumptions.

- Do not use pavement slab bounds as walkable width or stop a route inside an end wall. Intersect actual upward support with fixed full-height clearance and check connectedness to the real arrival.
- C3 ends at a real 2.09×1.70 m landing. A 1.35 m diameter upright envelope reaches arrival, and a separate 0.70 m envelope continues to the closed-door approach. The latter is not a 1.35 m route or passage through the leaf.
- Keep the terminal’s 20 mm floor/obstacle margins and 15 mm radius reserve explicit. Nine raster alias cells were corrected only after exact projected support verification; real exterior notches stayed blocked.
- Measure props and actors separately. C3 grounds one supporting carrier boot while the other remains about 33.67 mm above the floor in its retained walking pose; it does not plant both feet or simulate gait.
- R12 preserves road/pavement/terminal and all 369 repaired cobbles. A4b transfers A4a’s main-route result only because every other relevant owner is exact and its sole changed cell begins at z 2.615 m, above the tested 1.94 m band.
- New treads stay 25 mm behind the facade, with 310 mm depth and 140 mm rise; actual doorway seating is independently checked. Rebuild prior wear support/receiver/contact masks after architectural changes rather than translating caches.

**Ownership/coordinate contract:** Actual pavement/support, curb-normal sections, fixed obstacles, terminal landing and closed-door approach; World metric support z 0.180–0.195 m and fixed body band z 0.205–1.94 m; longitudinal samples at most 0.10 m; Recompute for changed support/obstacles; transfer only through exact geometry/control equality and a proved nonoverlap with the tested band.

**Not established:** Authored static design targets only: no code/accessibility certification, wheelchair manoeuvre proof, articulated gait, opening-door simulation or exact between-sample sweep. No opposite-frontage completion.

**Sources:** [r11_c3_final](../../qa/v0.1.9/evidence/r11_c3_final/C3_FINAL_REVIEW.md), [r11_c3_summary](../../qa/v0.1.9/evidence/r11_c3_summary/C3_technical_verdict.json), [r11_c1_terminal](../../qa/v0.1.9/evidence/r11_c1_terminal/C1_terminal_connected_envelope.json), [r11_c3_terminal_binding](../../qa/v0.1.9/evidence/r11_c3_terminal_binding/C3_terminal_geometry_binding.json), [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_summary](../../qa/v0.1.9/evidence/r12_a4b_summary/A4b_EVIDENCE_SUMMARY.json), [r12_a4b_contacts](../../qa/v0.1.9/evidence/r12_a4b_contacts/A4b_complete_aperture_cells_saved_joinery_contacts.json)

## 8. Close clipped paving while retaining its authored surface planes

Repair closure without replacing uneven paving by a whole-piece convex hull, and test final saved topography separately from preserved attributes.

**Observed scope:** C3’s 369 changed cobble owners and 471 raw components are closed positive solids; 38,849 retained-corner field checks pass and 5,137 top samples have a measured small tolerance.

- A whole-piece convex hull can produce an easy closed solid while flattening inherited dents. C3 rejected that shortcut and preserved original clipped surface planes.
- Separate exact retained corner/field checks from numeric geometry checks. The 5,137 sampled tops have maximum absolute deviation about 0.02442 mm; do not call every point bit-exact.
- Preserve already-closed topology through the final conversion. A closure gate before downstream per-face cleanup did not establish C2’s final edge incidence.
- Test closed incidence, consistent orientation, positive component volume and actual topography. A reported unmatched edge is not automatically a visible physical hole; inspect its geometry and image consequence.
- C3 road facts remain bounded; R12 merely preserves those owners. Pale tidy paving and broader pigment/wear remain open surface-design work, requiring newly derived support fields.

**Ownership/coordinate contract:** Each clipped original cobble component and its surviving oriented surface/attribute records; Original piece-local planes and actual saved top-surface world samples; Preserve concave dents and intentional source planes; add only required clipping caps and verify after final mesh conversion.

**Not established:** No universal road-repair or all-inherited-mesh guarantee; no new paving style, water simulation or opposite-frontage result.

**Sources:** [r11_c3_final](../../qa/v0.1.9/evidence/r11_c3_final/C3_FINAL_REVIEW.md), [r11_c3_summary](../../qa/v0.1.9/evidence/r11_c3_summary/C3_technical_verdict.json), [r11_c3_road_tolerance](../../qa/v0.1.9/evidence/r11_c3_road_tolerance/C3_road_tolerance_diagnostic.json), [r11_c3_frozen_builder](../../qa/v0.1.9/evidence/r11_c3_frozen_builder/build_R11.py), [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md)

## 9. Vary facade construction while checking actual seating and human scale

Use generated studies for form relationships, then govern the asset by actual saved proportions, support, joinery and material-specific planar construction.

**Observed scope:** Accepted T7 flat-lintel/three-light transom and T5 lower six-segment arch/taller narrow window supplement the original pilot at the unchanged actor/prop scale.

- Extract relationships from generated studies, not literal gloss, thick jambs, tall scale or invented dimensions. Actual measured geometry governs; generated pixels are not a construction specification.
- Vary head type, leaf panels, transom rhythm and window proportions while keeping broad stone planes, slim profiles and subordinate timber. T5 uses six unequal arch segments rather than a smooth tube or uniform triangulation.
- T7’s authored window opening is 0.94×1.36 m; T5’s is 0.84×1.48 m. Both door leaves are 0.90×2.10 m. These are asset dimensions, not operational clear-opening certificates.
- Measure real glazing perimeter overlap and bar ends, transom seating, knob attachment, leaf/landing meeting and step support. R12’s window rebate overlap is about 4 mm; visual plausibility alone was not enough.
- View held production plus neutral close and native hero. T5’s recessed leaf remains dark in unchanged lighting; a neutral proof reveals construction without licensing a production relight or declaring the whole street finished.

**Ownership/coordinate contract:** Declared module doors, transoms, glazing, timber members, stone surround, hardware and inward-set step; Metric module-local geometry, actual saved convex/perimeter seating and world context; Preserve protected props, actor pose and production presentation; regenerate dependent wear only after geometry acceptance.

**Not established:** No historical, ergonomic, building-code or operating-hardware certification; no live parametric preset or universal dimension defaults.

**Sources:** [r11_c3_final](../../qa/v0.1.9/evidence/r11_c3_final/C3_FINAL_REVIEW.md), [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_contacts](../../qa/v0.1.9/evidence/r12_a4b_contacts/A4b_complete_aperture_cells_saved_joinery_contacts.json), [r12_a4b_technical](../../qa/v0.1.9/evidence/r12_a4b_technical/A4b_TECHNICAL_REVIEW.md), [r12_a4b_builder_source](../../qa/v0.1.9/evidence/r12_a4b_builder_source/build_R12.py)

## 10. Freeze exact sources and distinguish opening from rebuilding

A reproducible checkpoint needs exact source, configuration, inputs and a fresh-copy replay; a packed scene and a compact evidence bundle have different dependency contracts.

**Observed scope:** A4b freezes 17 source/configuration files in a 23-file checkpoint and replays against exact C3; all 16 file-backed selected-scene images are packed.

- The exact C3 prerequisite is SHA-256 139776a6f399e3c4d9d1557c8e720cb6c19a87f53e847f2c582a9fdd31ab580a. Opening packed A4b does not need C3; reconstructing it requires that exact separate baseline and frozen source.
- A4b is deterministic Python-authored topology, not a live Geometry Nodes preset UI. The plugin’s manual recipe records do not execute it or install a compiler.
- Freeze every real dependency and verify resolved source/input paths in a fresh extracted copy. Compare the saved result after independent actual reopening, including protected globals, owner state and all 54 bones.
- The first A4b replay was killed before saving and produced no scene. Preserve it as an execution failure, not a semantic mismatch; the unchanged-source retry establishes the saved replay result.
- All sixteen file-backed images are packed and the audited active datablock inventory has no linked libraries, fonts, sounds, clips, volumes or cache files. Historical path strings and arbitrary custom/add-on code remain outside that inventory.
- The checkpoint manifest’s accepted:false is an earlier packaging stage; final exact-hash review supplies later acceptance without rewriting its bytes. Compact reports omit large raw forensic exports; scripts requiring those exports are not standalone portable tests.

**Ownership/coordinate contract:** Selected scene, exact frozen source/config, explicit C3 baseline and declared packed/active dependencies; File-relative fresh-copy source/input paths with explicit byte identities; defined saved semantic snapshot; Never replay by importing mutable live source or substituting a same-named baseline; preserve failed attempts and their actual outcomes.

**Not established:** No self-contained scene rebuild kit in this guidance/source ZIP, new-machine guarantee, unqualified dependency inventory or automatic operator.

**Sources:** [r11_c3_final](../../qa/v0.1.9/evidence/r11_c3_final/C3_FINAL_REVIEW.md), [r11_c3_replay](../../qa/v0.1.9/evidence/r11_c3_replay/C3_fresh_copy_replay_comparison.json), [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_delivery](../../qa/v0.1.9/evidence/r12_a4b_delivery/FINAL_DELIVERY_INDEX.json), [r12_a4b_checkpoint_manifest](../../qa/v0.1.9/evidence/r12_a4b_checkpoint_manifest/manifest.json), [r12_a4b_replay_sources](../../qa/v0.1.9/evidence/r12_a4b_replay_sources/A4b_independent_replay_source_audit.json), [r12_a4b_reopen](../../qa/v0.1.9/evidence/r12_a4b_reopen/A4b_independent_actual_replay_reopen.json), [r12_a4b_packed_assets](../../qa/v0.1.9/evidence/r12_a4b_packed_assets/A4b_selected_packed_dependencies.json)

## 11. Bind evaluated proof cameras to actual held and neutral images

A proof needs actual saved-source images, evaluated camera state and point projection checks; a target being in frame does not prove it is unobstructed.

**Observed scope:** All seven A4b final proofs are source-bound; rejected A3e and accepted A4b are compared in matching final offset cameras. Neutral overrides are explicit.

- Create a fresh unparented unanimated proof camera with explicit rotation mode, then evaluate aim, positive depth and required feature projections. Preserve the original production hero camera.
- Bind image/scene hashes, renderer/helper/config identities and original/rendered material/light/world/display/compositor state. Neutral diagnostics intentionally override presentation and must be labeled.
- Re-render relevant rejected and baseline comparators in the final camera when viewpoint changes could conceal a defect. A3e wedges remain visible in those matched cameras; A4b corrects them.
- Inspect actual held and neutral pixels, not only contact sheets, builder assertions or projection coordinates. C3’s real seam defect emerged in neutral proof despite valid functional tests and subdued production lighting.
- Required in-frame points do not establish full visibility: a lamp foot still overlaps part of a lower jamb/step corner. Disclose that occlusion and use saved contact geometry to cover the region rather than claiming every detail is visually clear.

**Ownership/coordinate contract:** Fresh diagnostic camera, evaluated target/feature points, exact production camera and held state; Explicit rotation representation, positive-depth normalized projection and original/rendered state hashes; Keep diagnostic overrides out of the selected saved scene; match historical comparators in the same proof camera.

**Not established:** No new image review or rendering by this package; no inference that every projected feature is visible or that diagnostic lighting is the production result.

**Sources:** [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_image_binding](../../qa/v0.1.9/evidence/r12_a4b_image_binding/A4b_IMAGE_BINDING_VERIFICATION.json), [r12_a4b_replay_pixels](../../qa/v0.1.9/evidence/r12_a4b_replay_pixels/A4b_SELECTED_REPLAY_PILOT_VERIFICATION.json), [r12_a4b_matched_t5](../../qa/v0.1.9/evidence/r12_a4b_matched_t5/A4b_T5_vs_A3e_VERIFICATION.json), [r12_a4b_matched_t7](../../qa/v0.1.9/evidence/r12_a4b_matched_t7/A4b_T7_vs_A3e_VERIFICATION.json), [r12_a4b_camera_source](../../qa/v0.1.9/evidence/r12_a4b_camera_source/render_R12.py), [r11_c3_final](../../qa/v0.1.9/evidence/r11_c3_final/C3_FINAL_REVIEW.md), [r11_c3_seam_addendum](../../qa/v0.1.9/evidence/r11_c3_seam_addendum/C3_frontal_line_addendum.md)

## 12. Separate exact saved semantics from evaluated UV and image variation

State the representation and tolerance of each reproducibility claim; exact saved scene state does not imply byte-identical files, evaluated UVs or rendered pixels.

**Observed scope:** A4b and fresh-copy replay have exact defined saved semantic state and 54 bones, while inherited live bevel UV evaluation varies slightly and the matched pilot images differ at 92/800,000 pixels.

- Selected A4b SHA-256 is 1818c2f4484b12512af49460ac0d1726fff3be95a21ddb521edc97b60793829e; replay binary is e3238e23508c2aafd96aa623ca79839fdcd04d5bd5c0d1f0e59d8c0a2873b98d. Both share defined saved semantic SHA-256 f34bc236ebf968916e8651491bc979c70c9b5da6536a129b7a76ff2185cbf838.
- Tuple/list JSON normalization is representation handling without numeric rounding. It does not license rounding changed coordinates or attributes until snapshots match.
- Inherited bevel evaluation preserves saved/raw fields and evaluated geometry/normals but can vary interpolated UV values. The active R02_MaterialLocal field drives a 1254×1254 pigment image; maximum observed 2.384185791e-7 UV equals about 0.000298977 texel under that actual unscaled mapping.
- Keep the active brick UV variation distinct from the earlier inactive new-shell UV replay failure and A2c’s deliberate reparameterization. Evaluated corner counts vary between openings; they are not a fixed universal discrepancy.
- Actual matched selected/rebuilt pilot images differ at 92 of 800,000 pixels, maximum 1/255 per 8-bit channel, with mean absolute channel difference 0.0000383333 in 8-bit code units. This is measured repeat/rebuild variation, not pixel identity.
- Matching camera/configuration, held controls, projections and proof-source hashes make that comparison attributable. They do not establish that UV roundoff caused every changed pixel; no ULP-count, universal evaluated-byte or cross-platform determinism claim follows.

**Ownership/coordinate contract:** Exact saved object/global fields, raw/evaluated attributes, actual material graph and matched rendered image pair; Saved numerical representation without rounding; separate evaluated UV coordinates, image texels and 8-bit channel levels; Preserve inherited live modifiers and report measured differences rather than silently changing source or widening an unspecified tolerance.

**Not established:** No pixel identity, evaluated-float identity, universal repeat floor, cross-platform determinism or causal attribution of each changed pixel to UV roundoff.

**Sources:** [r12_a4b_final](../../qa/v0.1.9/evidence/r12_a4b_final/A4b_FINAL_REVIEW.md), [r12_a4b_technical](../../qa/v0.1.9/evidence/r12_a4b_technical/A4b_TECHNICAL_REVIEW.md), [r12_a4b_summary](../../qa/v0.1.9/evidence/r12_a4b_summary/A4b_EVIDENCE_SUMMARY.json), [r12_a4b_reopen](../../qa/v0.1.9/evidence/r12_a4b_reopen/A4b_independent_actual_replay_reopen.json), [r12_a4b_uv_usage](../../qa/v0.1.9/evidence/r12_a4b_uv_usage/A4b_evaluated_uv_material_usage.json), [r12_a4b_replay_pixels](../../qa/v0.1.9/evidence/r12_a4b_replay_pixels/A4b_SELECTED_REPLAY_PILOT_VERIFICATION.json), [r12_a4b_delivery](../../qa/v0.1.9/evidence/r12_a4b_delivery/FINAL_DELIVERY_INDEX.json)

## Checkpoint roles and limits

- Exact selected R12 A4b scene: 1818c2f4484b12512af49460ac0d1726fff3be95a21ddb521edc97b60793829e
- Exact C3 replay input: 139776a6f399e3c4d9d1557c8e720cb6c19a87f53e847f2c582a9fdd31ab580a
- Final R12 review: 542fa2433aace15224c0ae7723eb185596e6b20aa05ae580fc76ae86c232dede
- Defined saved semantic digest: f34bc236ebf968916e8651491bc979c70c9b5da6536a129b7a76ff2185cbf838

Large scenes, proof PNGs and complete native/source delivery remain external with byte identities in [the external inventory](../../qa/v0.1.9/external_asset_inventory.json). This source ZIP is not a native-scene backup or complete reconstruction kit. Compact result reports refer to some excluded large forensic exports; no claim is made that those forensic scripts can run independently from this bundle.

No broader street completion, opposite-frontage result, new causal wear, paving pigment pass, accessibility certification or all-inherited-mesh cleanliness is established. Frozen R10 wear must remain disabled or be explicitly regenerated on accepted changed architecture. Later geometry cannot inherit acceptance merely from a shared generator.
