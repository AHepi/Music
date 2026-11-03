# 49 Research: how environment artists make a place old, used and full

What this file is: what people who build places for films and games do before and while they build, read from their own write-ups, course outlines, talks and tool manuals (3 November 2026, web research; sources at the end). Written to answer one question: why do our builders' places lack detail, and what do the professionals do that ours do not? Plain words throughout; a word list at the end.

## The short answer

Professionals do not add detail at the end. They start from a wall of real photographs, decide the story of the place (who uses it, what happened here), write down what every surface is made of and how it has aged, and only then build. Detail then comes cheaply from a few sources they prepare in advance: photographed surfaces, strips of repeating trim (window sills, pipes, skirting), stick-on marks (stains, cracks, posters), and a store of ready-made parts. Wear is put where the world would put it, by a few rules (edges rub bright, hollows fill with dirt, water runs down), and then broken up by hand. Our builders start from a blank file, invent every surface in code in an hour, and have no store of parts, so they stop at the big shapes.

## 1. The order they work in

Every course and breakdown describes the same order:

1. **References first.** A course for environment artists lists reference boards (visual, material and mood) and a scene plan as the first deliverables, before any modelling. Film artists collect thousands of photographs for textures, lighting and building styles. One artist writes that after collecting references for the location he gathered references for the individual assets, materials and lighting, and that the reference keeps growing through the project.
2. **Analyse the references, then plan.** The same artist analysed his references and planned which methods, which repeating pieces and which materials he would use before starting the blockout.
3. **Blockout:** plain shapes for proportion and camera, called the most important and most neglected step. Ours do this well.
4. **Replace the blocks with real pieces:** a small kit of repeating parts (6 to 10 core pieces in the course), consistent scale, shared materials.
5. **Set dressing:** props, stains, signs. One studio artist calls it the icing on the cake, and says the number of props is limited by the schedule.
6. **Lighting and atmosphere,** then a critical look back.

Ours do steps 3 and 6 and skip 1, 2, 4 and most of 5. That is the shape of the gap.

## 2. What they study about materials

- **How light meets each surface.** Material study means watching how a surface reflects and absorbs light, how its colour changes with the light around it, and whether it is smooth and shiny or rough and matt. Artists are told to observe materials in daily life and keep notes.
- **How each material ages, and where.** From the scale-model and 3D weathering guides, the rules are few and physical:
  - Edges and corners wear first: paint chips and bright metal show on convex edges; dirt, dust and grime settle in hollows, joints and corners.
  - Streaks follow the forces on the object: gravity on walls, water flow on buildings. Rain carries dust down a surface and leaves it in the joints; rust forms where water runs, pools or is trapped, around fittings, drains, rivets and welds, and where the paint has been breached.
  - Dirt survives where rain cannot wash it: close to ridges, hinges and overhangs.
  - The setting decides the weathering: a desert ages things differently from a forest.
  - Restraint: the guides warn against making every panel line equally dark, against rust streaks everywhere, against burying the detail under the weathering.
- **Layering.** Weathering is built as layers over a clean base (dirt, then chipping, then rust, then dust), each with its own pattern, and variation is added so nothing repeats.

Texturing tools make these rules automatic: a "dirt" generator reads the model's curvature and occlusion (where surfaces face each other) and puts grime in crevices and edges; an "edge wear" generator reads curvature and puts bright wear on convex edges, with occluded areas masked out so the wear does not land in hollows. The Blender add-ons and tutorials say the same: wear follows curvature, dirt settles in cavities, and the result is broken up with noise so it reads as patchy rather than a uniform outline. (Blender's own nodes can read pointiness and occlusion, so a builder can do this without an add-on.)

## 3. Where detail comes from without modelling everything

- **Photographed surfaces,** tiling, with their relief. The base of almost every professional material.
- **Trim sheets:** one picture holding strips of repeating detail (a sill, a cornice, a pipe run, a skirting). Long thin parts of a model are mapped onto the strip; one artist made two trim sheets (brick and concrete; wood for windows and shopfronts) for a whole street. Professionals call trim sheets and decals the way to add the smallest level of detail.
- **Decals:** small pictures laid on top of a surface, with a see-through edge: a stain, a crack, a poster, a chalk mark, a number plate. One breakdown has three decal passes: scene dressing, environment decals, and decals for story elements.
- **Photo projection:** Ian Hubert's method, famous among Blender users: take one photograph of a real thing, build crude boxes behind it, and project the photograph onto the boxes; move the map so parts of the photo land on the parts of the model. Minutes per object, and it reads as real because it is.
- **Kitbashing:** a store of ready-made parts (bolts, vents, brackets, ornament) stuck onto plain shapes. Film model makers detail their miniatures this way; one artist used an ornament kit to speed up a street.
- **Trade-off:** all of these need the parts to exist before the build. That is what a studio's library is, and what our sealed builders do not have.

## 4. Set dressing: every object placed for a reason

- The idea has a name, environmental storytelling: set dressing used to make small, self-contained scenes that a viewer pieces together. A level-design talk describes it as staging a space with properties that can be read as a meaningful whole.
- The working questions are: what is the history of this place, who lives here, what are their struggles. Don't just place a table; put on it the things that tell who sat there.
- Placement, condition and material of a prop carry the story: where it is, whether it is broken or clean or used, what it is made of.
- A theatre analogy from a forum: scenes are backdrops to a play; one or two props (Hamlet's skull) can tell the whole story.
- Restraint again: an Arkane artist warns that too much story and detail on one asset reads as visual noise once the whole set is dressed.

Our plugin placed weeds, litter and puddles by rule, with no story. The self builders placed sandbags by the gate and shells by the gun because they knew what a camp is. That is this principle, half applied: they stopped after the big props.

## 5. Big, medium, small

Artists sort detail into three sizes: primary shapes set the silhouette (squint and only these remain), secondary shapes give the thing its character, and the smallest shapes carry the story or the finish. They model in that order and check that each size is present, with areas of rest between areas of detail. A scene that has only the first size (ours) reads as a model; one that has only the third reads as noise.

## 6. The painted look, from people who have done it

Dishonored (Arkane) is the best-known painted-but-solid look in games. Its texture artists start from a photograph, filter out the noise while keeping the sharp edges, then paint over it with painterly brushes; the art director's rule was to avoid procedural generation and the direct use of photographs. The Arcane series (Fortiche) is a blend of physically based materials and hand-painted textures, with the paint carrying the style. In both, the detail is real (sculpted or photographed) before it is painted. Neither relies on a filter at the end, which is what all our builders did.

## 7. What this means for us

The missing detail has three kinds, and each has a different remedy:

| Kind of detail | What ours lack | What the professionals do | Cheapest remedy for the kit |
|---|---|---|---|
| Surface (texture, wear) | code-made colours, flat walls | photographed surfaces, wear by rule then by hand | a shelf of photographed surfaces in the kit; a one-page wear sheet (section 2) |
| Objects (parts, props) | plain boxes, few props | a store of parts, trim sheets, decals, kitbashing, a story that places them | a second pass by a set-dressing builder with a story brief; a small store of parts |
| Air (light in the air) | one even haze | light through a gap, dust, mist near the ground | already in the traps page; needs time, not tools |

And one change to the order of work: references and a material list before the build. A sealed builder has no internet, so the reference board for a place has to be made for it (by me, with web access, before its clock starts), and the material list can be its own first deliverable: every surface in the scene, what it is made of, how it has aged, where the wear sits.

## Word list

- **Blockout:** the place built from plain boxes to settle proportion and camera.
- **Reference board:** a wall of photographs of the real thing, kept open while building.
- **Material study:** looking closely at one real surface: how it takes light, how it ages.
- **Weathering:** the marks of age and use on a surface (dirt, chipping, rust, streaks, fading).
- **Curvature:** how sharply a surface bends; convex edges and concave hollows. Tools read it to place wear.
- **Occlusion:** how much a point is shut in by surfaces around it; tools read it to place dirt.
- **Trim sheet:** one picture of strips of repeating detail, mapped onto long thin parts.
- **Decal:** a small picture laid on a surface with a see-through edge (a stain, a poster).
- **Photo projection:** throwing a photograph onto plain shapes from the camera's direction.
- **Kitbashing:** detailing a model with ready-made parts from a store.
- **Set dressing:** placing props, stains and signs so the place reads as used by someone.
- **Primary, secondary, tertiary:** big, medium and small shapes; silhouette, character, finish.

## Traps

- A rule-made weathering system is what the plugin's dressing was; the professionals' rules are the same, but a person breaks them up by hand and places the story. Rules without a hand gave us noise once already.
- Decal and trim packs sold online are mostly science-fiction; for 1915 Britain the shelf would have to be made (photographs, Poly Haven, own decals).
- The research says "restraint" as often as it says "detail". A camp with every surface streaked is as wrong as a clean one.
- Builders are sealed (no internet). Any reference board or shelf must be in the kit before the clock starts.

## Sources

- Staffordshire University, module descriptor for a real-time environment art module (reference boards, blockout, modular kit, set dressing): https://evision.staffs.ac.uk/module_descriptors/GDEV50076.html
- 80.lv, "Creating a realistic 3D environment of an Ankara street" (reference, analysis, blockout): https://80.lv/articles/breakdown-creating-a-realistic-3d-environment-of-an-ankara-street
- 80.lv, Daniel McGowan, "The stages of environment art in gamedev": https://80.lv/articles/the-stages-of-environment-art-in-gamedev
- 80.lv, Tyler Anlauf, modular Roman environment (the blockout): https://80.lv/articles/001agt-004adk-17th-century-roman-modular-environment-in-ue4
- Hitem3D, environment art for film and VFX (reference boards, set dressing): https://www.hitem3d.ai/blog/Environment-Art-for-Film-and-VFX-Creating-Believable-Digital-Worlds
- Novedge, V-Ray weathering tips (dirt in crevices, edges first, environment decides, layering): https://novedge.com/blogs/design-news/v-ray-tip-enhancing-architectural-renders-with-realistic-aging-using-v-ray-weathering-techniques
- Adobe, Substance 3D Painter "Dirt" and "Metal Edge Wear" generators: https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/effects/generators/dirt and .../metal-edge-wear
- Stray Spark, procedural edge wear in Blender (wear follows curvature, dirt in cavities): https://www.strayspark.studio/learn/tutorials/procedural-edge-wear-blender
- Access Models, how to weather a model (streaks follow forces, restraint): https://accessmodels.co.uk/blogs/plastic-model-kits/how-to-weather-a-model-to-look-realistic
- Scale Model Shop, weathering guide (rust around fittings and drains, scale): https://www.scalemodelshop.co.uk/scale-model-weathering-guide-realism/
- DeAgostini, weathering tips (rust where rain runs and pools, at rivets and welds): https://blog.deagostini.com/?p=3944
- Vallejo "Rain marks" product note (rain carries dust into joints): https://archive.armorama.com/news/22998
- Game Maker's Toolkit, "How level design can tell a story" (environmental storytelling; Smith and Worch's definition): https://amara.org/videos/Lv64YfjMFhOC/en/3102784
- GDC Vault, Harvey Smith and Matthias Worch, "What happened here? Environmental storytelling" (2010): https://gdcvault.com/play/1012647/What-Happened-Here-Environmental
- Wayline, narrative level design (who lives here; don't just place a table): https://www.wayline.io/blog/tyranny-of-toolbar-narrative-level-design
- Polycount thread (scenes as backdrops to a play): https://polycount.com/discussion/comment/2703662
- 80.lv, environment storytelling in Dishonored 2 (too much detail is noise): https://80.lv/articles/environment-storytelling-in-dishonored-2/
- 80.lv, asset and material production in Dishonored 2 (painterly look, hand painting, no procedural): https://80.lv/articles/asset-material-production-in-dishonored-2/
- Polycount, Dishonored textures (start from a photo, filter, paint): https://polycount.com/discussion/comment/2156684
- Sci-Fi London, Sebastien Mitton interview (avoid procedural and direct photography): https://news.sci-fi-london.com/news/games/2012/09/dishonored-interview-sebastien-mitton
- 80.lv, Arkady Nabirenkov, cannon in the Arcane style (blend of PBR and hand-painted): https://80.lv/articles/creating-a-game-ready-cannon-in-an-arcane-inspired-style
- CGMA, Cliff Chen, SanXia Street (trim sheets, decal passes, ornament kitbash): https://cgmasteracademy.com/blog/how-to-use-impactful-decals-in-a-modular-environment-sanxia-street.html
- Blender Bros (decals and trim sheets for the smallest detail): https://www.blenderbros.com/resource_redirect/offers/bH42AJhG
- Wikipedia, kitbashing: https://en.wikipedia.org/wiki/Kitbashing
- Ian Hubert at the Blender Conference (profile), and CG Boost "Lazy photo projection" lesson: https://conference.blender.org/profile/967/ , https://academy.cgboost.com/courses/554515/lectures/24558934
- Steve Yang, composition notes (primary, secondary, tertiary; squint test): https://steveyang.readthedocs.io/Modeling/123/
- RocketBrush, drawing materials from reference (observe materials in daily life): https://rocketbrush.com/blog/how-to-draw-materials-mastering-references
