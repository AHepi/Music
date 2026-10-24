# BUILDER BRIEF: <PART NAME> (<one line: what this part is>)

What this is: the brief the planner gives one builder for one part of <PLACE>. Fill in every <...> and delete the comments.
The builder's folder is <FOLDER>; its collection is `Place: <OWNER>`; `place_owner` is `<OWNER>`; its stage file is
`stage_<OWNER>.py`. Time-box about <N> hours. This brief is one of several that run side by side: nobody touches another
builder's objects or materials.

## 0. Read first (about 20 minutes), in this order
1. The style note (`<path>/style-note.md`): its section 0 is the rule for every builder.
2. The facts table (`<path>/real-world-facts.json`): every size you build to, with its source and confidence.
3. The place settings (`<path>/place-settings.json`) and the ownership table.
4. The skill `surfaces-wear-and-construction`: its first screen, then `the-required-steps.md`.
5. The pictures or facts in section B.
The person's request, word for word: "<the request>".

## 1. Rules that hold for every builder
- You own only the objects, collections and materials listed in section C. Never rename or delete anything else. New objects:
  your collection `Place: <OWNER>`, the custom properties `place_owner` and `place_role`. Never edit a material or node group
  that anyone else uses: the kit copies it (`PK <role> / <surface>`).
- Frozen (nobody changes these): cameras, lights, the world, render settings, <the ground height from the ground part>,
  <anything else the planner names>.
- Seat things on the frozen ground with `pk.seat_on_ground`; build every part carried (planks on supports, supports on the
  ground); real sizes from the facts table.
- Run only tiny tests on this computer (small pictures, `--quick`); anything bigger goes to a rented card or waits.
- Spend no money. Never commit or push. Never write a key, an id or a personal detail into any file.
- Return your reports as text in your final answer (a helper may not be allowed to write report files); save evidence as
  JSON or text files as you go.
- Report each claim as a bare sentence ("every plank rests on at least two supports") and say which named tool measured it.
- Report in plain everyday words: what you did, tested, did NOT test, are unsure about, every failure, and the seconds of
  card time used.

## A. What you build (in PRIORITY ORDER; a finished step 1 plus 2 is already a valid delivery)
**Step 1 (about <N> min): <the main structure, from the bottom up>.** <sizes, supports, what stands on what>.
**Step 2 (about <N> min): <the shapes: bevels, no two siblings alike, damage and age as shape>.**
**Step 3 (about <N> min): <roles and surfaces>.** Give every object its role; run `explainer-film-place finish-part --owner
<OWNER> --save-as part.blend`.
**Step 4 (if time): <extras>.**
After each step the scene must be coherent. Say at the top of your report which steps you finished.

## B. Pictures or facts to follow, and not to copy
FOLLOW: <picture or fact and what it shows>.
DO NOT COPY: <what looks wrong in it>.

## C. You own / you must not touch
OWN: <objects, collections, materials>.
DO NOT TOUCH: <every other part, by name>. Contracts with other builders: <e.g. "inside 1.2 m of the lane's centre line the
ground stays as it is">.

## D. Surface notes (roles and surfaces)
Roles for your objects: <role list>. Surfaces: <surface per role, or "the kit's default">. Looks: <look per role>. Sizes of
bevels and tiles are in `place-kit/data/surfaces.json`.

## E. Guard numbers
<The numbers from the style note and the facts table that apply to your part: detail energy per region, value range, size
limits, marks that must be few and big, plants that may not grow where.>

## F. Preview views
Make cameras named `Place <OWNER> cam <n>` (the pass deletes them): <views to draw, sizes, samples>. One job per round, many
pictures in it.

## G. Deliverables
`stage_<OWNER>.py` with `apply(options)`: it works on the open scene and is idempotent (it first removes what it made
earlier, found by `place_owner`, and prints a short plain report of objects created, changed and deleted); a part report;
previews under 400 KB each.

## H. Your own checks before you hand over (numbers in your report)
Run on your staged scene and report each as PASS or FAIL with its numbers: `explainer-film-place construction`,
`explainer-film-place normals-test`, `explainer-film-place finish-part --owner <OWNER>` (its audit), the stage run twice
(same counts), and `explainer-film-place ownership-diff` against the ownership table. Look at your 100 percent crops with
the question: could this sit in a hand-painted game level next to the biggest, simplest thing in the place?
