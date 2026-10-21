# Skills scout: what on skills.sh is worth keeping for your work

Date of the survey: 21 October 2026. Nothing was installed. Everything below is "read, not installed": I read the skill text (and, for four of them, the helper scripts) but I could not test any of it.

Words used here:
- **Skill** = a text file of instructions that Claude reads before doing a job. Some skills also come with small helper scripts.
- **Install** = copying that folder next to your project (or into your home folder with `-g`) so Claude can find it.
- **skills.sh** = Vercel's public directory of skills. Its "installs" number is how many people ran the install command.
- **Audits** = three automatic scanners (Gen Agent Trust Hub, Socket, Snyk) shown on each skills.sh page. A pass is a weak signal, not a guarantee.

---

## 1. Short answer

How I looked: I ran about 120 searches with the skills.sh search tool (`npx skills find ...`), read the site's leaderboard, and then read the actual instruction files of about 37 packages (a "package" is one GitHub repository that holds one or more skills). Most of the site is aimed at web developers; the top of the leaderboard (grill-me, hyperframes, Azure, React) has nothing for your kind of work. The Blender material is small, new and little-used (tens to a few hundred installs each), so nothing here has a big crowd behind it.

Worth keeping, best first:

| # | What | Helps with | Maintainer | Popularity | Risk |
|---|---|---|---|---|---|
| 1 | **Scenario "Blender expert" set** (7 skills out of a 166-skill repo) | Your Blender 5.2 work: scripting rules, shader and mask layering, baking, geometry nodes, EEVEE lighting, shot planning, exporting a set to your three.js stage | Scenario (scenario-labs; a company that sells an AI game-art service). The Blender skills do not need its service. | 260 to 445 installs each; repo 1.1K GitHub stars; first seen 26 Sep 2026; all three audits pass | Low-medium, see below |
| 2 | **tmhsdigital: porting-to-blender-5, headless-batch-scripting, procedural-materials-and-shaders** | Stops Claude writing old Blender code that breaks in 5.x; running Blender with no window | One individual (TMHSDigital) | Tiny: 10 installs, 17 stars; first seen 24 Jun 2026; audits pass | Low |
| 3 | **el4cteo: blender-texture-baking** | Baking maps from a script, including packing roughness/metal/occlusion into one image | One individual (el4cteo) | 24 installs, 312 stars; first seen about 6 days ago; audits pass | Low-medium (new, tiny) |
| 4 | **github/awesome-copilot: noob-mode** | Plain-language reporting: explains every action, jargon and risk in everyday words, lists what changed and how to undo it | GitHub's community collection | 6.4K installs, repo 40.2K stars; audits pass | Low, but see the downside |
| 5 | **cloudai-x: threejs-textures and threejs-loaders** | Your three.js stage: loading models and images correctly with current three.js names | cloudai-x (an individual; unknown) | 11.5K to 11.7K installs, 3.7K stars; audits pass | Low |
| 6 | **elevenlabs/skills: text-to-speech and music** | Narration and score: chunk-to-chunk continuity, new voice model notes, plan-based music, music from a video | ElevenLabs itself (official) | 15.8K and 10.1K installs, 497 stars; audits pass | Medium: tells the agent to run an installer that signs in. Say no. |
| 7 | **runpod/runpod-plugins-official: pod-doctor and cost-audit** | Find out why a pod will not start without logging into it, and where the money is going | RunPod itself (official) | 1.8K installs each, 46 stars; first seen about 12 days ago | Low (cost-audit is read-only; pod-doctor can stop/delete only if told to). **Same repo you already have, so check your copy first.** |

Honest gaps (things you asked for where I found nothing worth keeping):
- Making a texture **seamless**, **non-repeating over a large area**, or building **moss / wetness / rubbish** recipes: no skill I read teaches these in Blender. The Scenario shading skill covers wear, grime and dirt as layered masks, but not moss, wetness or tiling.
- **Measuring how close a texture is to a reference picture**: nothing usable. The few tools are either a model's opinion (not a measurement) or compare videos only. A small script of your own (colour statistics plus a similarity score) would beat all of them.
- **Filming a three.js scene frame-by-frame in headless Chromium**: the Playwright skills do not cover WebGL flags or frame-exact capture. The one good idea I found (render by setting the time yourself, never by the wall clock) is tied to another company's tool.
- **fal, masks, stamp sheets, style consistency**: no good generic skill. You have the Fal connector, which already searches models and prices.
- **GitHub repo hygiene**: nothing beats what Claude already does with `gh`.

---

## 2. The keepers in detail

### 1. Scenario Blender expert set

What it is: inside the repo `scenario-labs/skills` there is a folder of 15 Blender skills written for Blender 5.2 LTS (the README says tested on 5.2.1). They are meant to be installed together, because the specialist skills borrow helper scripts from the main "expert" skill.

What I read, and what is in it:
- **scenario-blender-expert** (the main one): how to run Blender two ways (open window, or no window with `blender -b`), plus a list of traps in Blender 5.x (for example the render engine name `BLENDER_EEVEE`, not `BLENDER_EEVEE_NEXT`; removed `action.fcurves`; compositor now a node group). It says which sculpt tools crash with no window. It insists on looking at a render before saying "done".
- **scenario-blender-texturing-shading**: shading as black-and-white masks feeding colour, roughness and height; wear, grime and chipping layers (a helper called `add_wear`); colour-space rules (data maps are "Non-Color"); a hand-painted stylised look built from a curvature mask and a baked emission; painting into the UV map from a script; bake last. Numbers and quality checks are given. It does not cover moss, wetness or seamless tiling.
- **scenario-blender-uv-baking**: bake from high to low detail, a small test bake before the big one, 16-bit PNG, margin and occlusion distance rules, OpenGL vs DirectX normals, and checks for inverted or blank results. Does not cover roughness or height bakes or tiling.
- **scenario-blender-geometry-nodes**: building node trees from Python (scatter, array along a curve, growth, simulation), with check steps that count what was made. Aimed at 5.2.
- **scenario-blender-lighting-rendering**: EEVEE vs Cycles settings, light leaks, AgX colour, render passes, compositor, toon looks, "value" (light/dark) checks.
- **scenario-blender-export**: exports with a "web" preset (glTF with compressed meshes and WebP images) and then re-opens the file to check it matches. Handy for moving a Blender set to your three.js stage. It does not cover baking procedural materials first, nor Draco/KTX compression.
- **scenario-blender-previs-storyboard** (optional): shot sizes, lens choice, eye-line and "is the subject blocked" checks, contact sheets, a rough animatic. This is the closest thing I found to "shot composition checks" for a 3D set. I read it in full.

Why it ranks first: it is concrete (named functions, numbers, checks), current (mentions a date of 18 Oct 2026), headless-friendly, and its scripts do not touch the network. I read two of the helper scripts through a summary tool: `bx_audit.py` (about 430 lines) and `bx_materials.py` (about 900 lines). Neither uses the network, runs other programs, deletes files or hides its code. One detail: `bx_audit.py` has an import step that resets the open Blender session without asking, which is harmless when run with no window and would wipe unsaved work if run in a window you are using.

Things to know before installing:
- Install only the Blender ones. The other ~140 skills in that repo are for Scenario's paid service (they need a Scenario account or API key).
- Every one of these files contains the line "if a sibling skill is missing, run `npx skills add scenario-labs/skills --skill <name>`; if nobody is watching, carry on and flag the gap". That lets an agent install packages by itself. Tell Claude not to.
- Do not install `scenario-blender` or `scenario-blender-blockout`: they use a Scenario add-on and send work to outside video services, and the README does not say what happens to your data.
- Many numbers are tagged "[verified]" or credited to named artists, but the files show no evidence. Treat them as good starting values, not facts.
- It is about four weeks old; expect it to change.
- I did not read the other helper scripts (`bx_gui`, `bx_review`, `bx_uvbake`, `bx_gn`, `bx_light`, `bx_previs`, `bx_export`).

Install command (run it yourself, in the folder you want it in; add `-g` to put it in your home folder instead):
```
npx skills add scenario-labs/skills -a claude-code -s scenario-blender-expert scenario-blender-texturing-shading scenario-blender-uv-baking scenario-blender-geometry-nodes scenario-blender-lighting-rendering scenario-blender-export scenario-blender-previs-storyboard
```
Note: the installer first downloads the whole repository into a temporary folder (about 80 MB when I saw it), then copies only the chosen skills.

### 2. tmhsdigital: three Blender 5 skills

What I read:
- **porting-to-blender-5**: a table of about 25 things that changed or were removed between Blender 4 and 5.2 (for example `import bgl`, `scene.node_tree`, `sequence_editor.sequences`, the 5.2 removal of `mod["Socket_1"]` on node modifiers), and a short snippet that works on both. It tells Claude not to guess with `hasattr`.
- **headless-batch-scripting**: the exact command shape for running with no window (`--background --factory-startup --python-exit-code 1`), why a failed script still reports success without that last flag, how to pass your own options after `--`, how to find the version, and a full batch render script.
- **procedural-materials-and-shaders**: how to build a material from Python on 4.5 LTS and 5.2 (socket names, the new Principled BSDF names, `use_nodes` being phased out, node groups, when you must use an operator such as baking). It lists eight mistakes AI tools typically make. Its version notes mix "5.x", "5.1" and "5.2 LTS", and it states some future plans (removal in Blender 6) as fact, so check those against the release notes.
- The same repo also has `bake-high-to-low` and `vse-python` (Blender's video sequencer). I did not read them.

Why keep it: it is the best "do not write old Blender code" safety net I found, and it matches how you work (scripts, no window). Why it ranks second: one person's repo with almost no users, so it may go stale. The facts are checkable against Blender's own release notes.

Install (run it yourself):
```
npx skills add tmhsdigital/blender-developer-tools -a claude-code -s porting-to-blender-5 headless-batch-scripting procedural-materials-and-shaders
```
If you install both this and the Scenario set, the main overlap is the list of Blender 5 traps; that is fine, they agree where I could compare (EEVEE name, removed `action.fcurves`, `scene.node_tree`).

### 3. el4cteo: blender-texture-baking

What I read: a concrete guide plus a ready-made script, `scripts/bake_maps.py` (about 190 lines, plain readable code), that bakes normal, occlusion, roughness, emission, "combined", position, curvature, thickness, an ID map, and also base colour, metal and opacity by a temporary trick through an emission shader. It can also bake a procedural material onto itself with no high-detail mesh ("self-bake"), which is relevant to you. It can pack occlusion/roughness/metal into one image ("ORM"). It includes a "symptom, cause, fix" table (wavy cylinders, black patches, neighbour bleed, banding fixed by 16-bit). It says the right colour space for each map.

What it lacks: height maps and specular are not supported. No tiling.

Safety: I read the script through a summary tool: no network, no running other programs, no file deletion. It depends on a second file (`_bpyx`) that I could not read, and it loads that file from its own folder, so only run it from an untouched copy.

Why only the one skill: the repo has 22 Blender skills (blender-core, blender-pbr-materials, blender-geometry-nodes and so on). I read `blender-core` and `blender-pbr-materials` too: both concrete and aimed at 5.2, but they mostly duplicate #1. The baking one adds a ready script, so it is the one I would add.

Install (run it yourself):
```
npx skills add el4cteo/blender-skills -a claude-code -s blender-texture-baking
```
Popularity: 24 installs, 312 stars, first seen about 6 days before this survey.

### 4. noob-mode (plain-language reporting)

What I read: a behaviour file for people who are not programmers. Before each action that needs permission, Claude writes a small block: what it wants to do, why, a risk level, and what happens if you say yes or no. Jargon gets a one-line explanation the first time. Multi-step work starts with a numbered plan. Errors come back as "what went wrong / what it means / what we can do". Every task ends with a list of files created, changed and deleted, and how to undo it. It ships a glossary of 100+ terms and 15 examples (I did not see those two files).

Downsides, said plainly:
- It adds an approval-style routine to everything, which would be tiresome in long automated runs. Switch it on for sessions where you want hand-holding, off otherwise.
- It limits explanations to a sentence, may soften warnings with a reassuring tone, and does not show raw output unless you ask. For anything important, ask for the raw output too.
- It does not tell you how to check that the result is correct.

Install (run it yourself): the installer downloads the whole repository temporarily, and this repo is a big community collection (I did not measure it), so check free disk space first.
```
npx skills add github/awesome-copilot -a claude-code -s noob-mode
```
I looked at several alternatives (a strict "20 words per sentence" skill, Anthropic's `internal-comms`, handoff skills). None fit as well. See section 3.

### 5. cloudai-x: threejs-textures and threejs-loaders

What I read: both state they target three.js r186 and use modern names (`colorSpace`, not `encoding`; `HDRLoader`, not `RGBELoader`). Textures: loading, colour space for colour vs data images, wrapping and repeat, mipmaps and sharpness at angles, canvas and video textures, environment maps, render targets, freeing memory, plus a "common mistakes" list. Loaders: GLB loading with Draco, meshopt and KTX2 compression, loading progress, caching, cloning and cleaning up, and the newer WebGPU path. Both are long, mostly working code, no scripts, no network calls of their own.

Why keep: your stage already works, but this gives Claude current names and the usual traps (wrong colour space makes repainted images look washed out). It does not teach projecting a repainted picture back onto 3D (none of the three.js skills I found do). I did not read the other skills in this family (materials, lighting, shaders, animation), so install only the two I read.

Install (run it yourself):
```
npx skills add cloudai-x/threejs-skills -a claude-code -s threejs-textures threejs-loaders
```

### 6. ElevenLabs official: text-to-speech and music

What I read: Text-to-speech names the current model (`eleven_v4`), says it has no speed control and no SSML (so pacing comes from punctuation and tags like `[whispers]`), explains `previous_text` / `next_text` to keep tone across separately generated pieces, number and date reading, output formats, and cost counting. Music explains the newest model, composition plans (up to 30 sections with style words and length per section), music built from up to ten videos, and filling in a gap in a track. The sound-effects skill also exists (0.5 to 30 seconds, loopable); I read it but did not shortlist it.

Honest value: moderate. You already narrate with ElevenLabs, so keep this only if you want Claude to be reminded of continuity between chunks and of plan-based music. The music skill says it has no stem separation and gives no licence terms.

Risk to avoid: each file tells the agent to first run `npx -y @elevenlabs/cli@latest onboard init`, which signs you in and stores a key for the project. That is a fetch-latest-and-run step with login. You already have the connector, so tell Claude to skip it.

Install (run it yourself):
```
npx skills add elevenlabs/skills -a claude-code -s text-to-speech music
```

### 7. RunPod extras: pod-doctor and cost-audit

These are from the same official repo you already have (`runpod/runpod-plugins-official`). They were added about 12 days before this survey, and the RunPod skills listed in this session number about nine (runpod, runpod-mcp, runpodctl, flash, companion-clis, runpod-usage, runpod-templates, runpod-migrate), so check whether you have them before installing.
- **pod-doctor**: read the state and logs of a failing pod and quote the deciding line; by default it stops rather than deletes (the page says deleting also deletes the pod's disk); it must not touch a pod you did not name. It does not mention SSH.
- **cost-audit**: strictly read-only; checks pods, serverless endpoints, network volumes and billing history to show where money goes; it hands any fix to another skill only after you agree. It uses the RunPod MCP tools.
- The page for the related `pod-deploy` skill shows a Snyk "warn" (no reason given), so I would not add that one without looking.

Install (run it yourself, only if missing):
```
npx skills add runpod/runpod-plugins-official -a claude-code -s pod-doctor cost-audit
```

---

## 3. Looked at and not worth it

One line each (what, installs, why not). "Read" means I read the skill text; "listing only" means I only saw the search listing or the skills.sh summary.

Blender and 3D
- roble3/cc-blender-skill (30 skills; 1.4K installs; 109 stars; audits pass). Read: materials, reference-look-calibration, reference-analysis-validator, README. Needs a live Blender connection (no window-less use) and runs generated code inside your open Blender with no review step. Tested on 5.1.1. Its "compare to reference" checks only measure silhouette overlap and colour stats on logos and mascots, not texture detail.
- vladmdgolam/agent-skills blender-mcp (2.3K; Snyk warns, no reason). Read the top of it. Live-connection only (your Blender link timed out in this session anyway); the export part was hidden.
- sfkislev/flue Blender (2.8K; 98 stars). Read the top. Needs a separate Python package (`flue`) and a live bridge; one tool for many apps, including Office.
- jablonkai/skills blender (50). Read. Concrete and tested on 5.2.2, but its helper accepts any code sent to a local port with no password, so any web page you visit could in theory poke it; live session only.
- ra100/blender-claude-plugin shader-nodes (40). Read. Recipes are fine but it is built around a live connection, has no baking, procedural textures are thin, and one line is corrupted.
- arjun988/blender-skills (363 stars). Read hand-painted-style: about 150 words of general advice ("paint values into the albedo"), no steps. Thin. The materials page was equally general.
- xliuxjianx/blender-production-skills blender-npr-eevee (9). Read. A real toon-fill plus outline recipe, but narrow, half governance text, and it leans on sibling skills that are not included.
- bradyajohnston/nodebpy (4 installs; Gen Agent Trust Hub warns, no reason). Read. A Python library that writes node trees as code. Needs `pip`/`uv` to install the library and Blender as a Python package (a big download). Interesting later, not now.
- bbeierle12/skill-mcp-claude shader-noise (117). Read. A good noise reference, but in GLSL (web shader code), not Blender.
- freshtechbro/claudedesignskills blender-web-pipeline (3.3K; 1.1K stars). Listing only: the body was hidden. Generic "export to the web" wording.
- hkuds/cli-anything, composio-community, mattjamo/bpy_skill, samuelasherrivello/ai-skills-blender (repo is about 500 MB), kajisho5, ifbars: not read (see section 4).

Web 3D, browser and film
- microsoft/playwright-cli (191K). Read. Can record video and run page code, but says nothing about WebGL flags, deterministic time or frame-stepping; video is real-time. You already film headless.
- anthropics/skills webapp-testing (183K). Read. Basic headless Chromium plus a server starter; no video, no WebGL.
- currents-dev/playwright-best-practices (96K). Read the index only: it points to about 55 files, one on canvas/WebGL and one on image comparison, which I did not open.
- digitalsamba/claude-code-video-toolkit ffmpeg and playwright-recording (11K, 1.3K). Read. Written for a different tool (Remotion). Misses image-sequence-to-video, mixing and fades; recording is real-time. Its `runpod` skill covers serverless endpoints only, with no pods or volumes.
- heygen-com/hyperframes `three` (69K installs, 68K stars). Skills.sh summary only. Right idea (the page sets the time and the scene draws that exact frame) but tied to HeyGen's own video tool, which competes with your pipeline. I could not find the file path.
- playcanvas/skills verify-pixels (243). Read. Good method (capture the same frame twice and prove the two are identical; report exact pixel counts), but it uses PlayCanvas commands. Steal the idea; do not install.
- scottstts/threejs-awesome-graphics (86 to 89): image-pipeline is only effect ordering, procedural-materials is a routing page with no code, camera-direction has rules for camera rigs but no shot design. Read all three. The repo is about 260 MB.
- iart-ai/motion-design-skills shot-composition (2.5K). Read. Concrete grid, safe-area and parallax numbers, but for flat motion graphics, not 3D sets.
- fal-ai-community/skills cinematography (1K). Read. A vocabulary list that relies on an outside `genmedia` command and three files I could not see; maintainer not stated.
- samber/developer-relations-skills technical-video-script (8.2K). Read. About 6,500 words for developer-tool videos, starts with a 13-question interview and writes its own notes file. Does not fit your pipeline.
- sonilo-ai/skills audio-ducking (1.2K). Read. Needs a paid Sonilo account and uploads your audio to their server; ducking is also easy with free ffmpeg. Page tells the agent not to announce which route it uses, which I do not like.

Images and fal
- affaan-m/ecc fal-ai-media (9.5K). Read. Names Nano Banana 2 and Pro, not Flux; uses an `npx -y fal-ai-mcp-server` with the key written in plain text in a config file; you have the Fal connector already. Its video-editing skill (13.6K) has decent ffmpeg loudness lines but also contains odd off-topic orders (DAW saves, MIDI checks, telemetry); I would not use it.
- rehan-remade/universal-modder fal-assets and asset-pipeline (1.3K each; 8.5K stars). Read. Lists useful-looking fal model names (a tiling model, a PBR model) but depends on an undocumented `um` command line tool built for game mods; ask the Fal connector for models instead.
- layerai/skills layer-textures (3K; Snyk warns). Read via summary. Needs the Layer.ai service; its one concrete tip is to pick a "tileable" model.
- gregory-esman/ai-film-pipeline banana-pro-director (44). Read about the first 100,000 characters. Written for Higgsfield's paid service and pushes photorealism. Some ideas carry over (one fixed reference, change one thing at a time).
- 101-skills / magentosh / qu-skills "superpowers" copies of ai-image-generation (300K to 820K installs each): not read; they appear to be copies of each other and sit on a different service (inference.sh), not fal.

Measuring and comparing
- yeachan-heo/oh-my-claudecode visual-verdict (873). Read. A model's score out of 100 for a UI screenshot; no formula, so results vary run to run.
- daymade/claude-code-skills video-comparer (938). Read. Scores two videos with PSNR and SSIM (standard similarity numbers) and builds an HTML report; videos only.

Writing, notes, GitHub
- anthropics/skills internal-comms (79K). Read. Company-newsletter and "3P update" formats, not plain-language reports.
- dobroslavradosavljevic/skills plain-language (51). Read. Strict aerospace-style English (20-word sentences); too rigid. noob-mode fits better.
- mattpocock/skills handoff (1.0M) and grill-me (1.4M). Skills.sh summaries only. Programmer-oriented: handoff writes a summary for the next session into a temp folder; grill-me interviews you about a plan. Popular, not matched to you.
- trailofbits/skills gh-cli (6.5K). Read. Tells the agent to use `gh` rather than raw web fetches; hooks not seen. You already have `gh` set up.
- affaan-m/ecc github-ops (8.5K). Read. A sane maintainer routine, but it auto-closes quiet issues after 30 days and creates releases and tags; has a fixed 2026-03-01 date inside it.
- microsoft/azure-skills, vercel-labs, heygen-com and lark skills at the top of the leaderboard: irrelevant to your work.

---

## 4. Not checked

- **More than 20 packages and families I only saw in search results** (or whose files I could not reach) and never opened: hkuds/cli-anything, mengto/skills (3d-wood-material, 3d-high-resolution-textures, browser-video-recording), majidmanzarpour/threejs-game-skills, gamedev-skills (threejs-scene-setup), img2threejs, enzed/r3f-skills, composio-community/opencode-skills, mattjamo/bpy_skill, ifbars/blender-agent-studio, freshtechbro substance-3d-texturing, remotion-dev/skills, vercel-labs/agent-browser, openai/skills (playwright), software-mansion/argent screenshot-diff, mckruz/comfyui-expert, prime-skills/runcomfy-agent-skills (nano-banana-2, flux-kontext at 430K+ installs), calesthio (generative-media-skills and openmontage), meodai color-expert, jezweb image-processing, mindrally computer-vision-opencv, eachlabs seamless-pattern-generation (211), summerengine tileable-texture (7), riekelt technical-writer family (about 17K installs each; could not find the file paths), trailofbits open-sourcing, marcfargas repo-hygiene.
- **Disk problem on my side.** Early on I cloned about 30 repositories into the scratch folder to read them, and two (about 500 MB and 260 MB) filled the machine's disk. Following the coordinator's order, I deleted every clone, stopped cloning, and read the rest only through skills.sh pages and raw file addresses (plus `npx skills add <repo> --list` for two small repos). The scratch folder now holds only my search lists. A few packages that I had cloned were lost from reading as a result (listed above).
- **Several reads were through a summarising reader**, not a straight copy of the file. The helper-script reviews (four scripts) and the "no scary instructions" checks are that reader's findings, not my own line-by-line check. Where the page was cut off ("Show more"), I say so.
- **Helper scripts I did not read:** Scenario's `bx_gui`, `bx_review`, `bx_uvbake`, `bx_gn`, `bx_light`, `bx_previs`, `bx_export`; el4cteo's `_bpyx`; every script in the other packages.
- **Dates:** skills.sh shows "first seen" but not "last updated", so I cannot say how fresh most packages are. Scenario's files mention 18 Oct 2026, so that set is current as of this survey.
- **The installer itself.** The `skills` command's help text mentions an install "telemetry event" (an anonymous ping). I did not inspect what it sends. It also has a `skills use <package>@<skill>` command that is said to make a prompt for one skill without installing it; I did not try it. If you want to test before committing, that is the thing to try first.
- **Nothing was tested.** I could not run Blender here (your Blender connection timed out in this session), so no claim above is "it works"; all are "the text says".
- **Facts from my own background, not from what I read:** I believe the owner of nodebpy is the author of the Molecular Nodes add-on, but nothing I read says so.
