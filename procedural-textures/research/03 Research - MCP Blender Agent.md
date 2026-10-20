# 03 Research - MCP Blender Agent

Written 19 October 2026. Everything marked "ran" was run on this machine (Linux, 4 processor cores shared with other helpers, no graphics card, Blender 5.2.2 started without a screen). Anything I only read in the code or on a web page is marked "read" or "not run".

## The short answer

**MCP Blender Agent is a small, real, free (MIT licence) tool that lets an AI assistant run Blender by calling about 216 ready-made commands ("tools"), such as "create a material", "add a bone" or "bake", instead of writing a Python script each time.** It is a one-person project, three months quiet, and its main aim is rigging and animation for game-engine work (Unreal Engine 5), not textures.

For **our** job it does not help, and in places it is worse than what we already do:

* **It cannot do the part of a texture recipe that matters most.** It can add a node and set the plain number sockets on it, but it has no tool to set a node's *settings* (the Noise type, the Math operation, the Mix blend mode) or to set the stops of a Colour Ramp, and it cannot make a reusable node group with named inputs and outputs. I ran each of these and they fail. Our recipes need all of them.
* **A toy brick tile took 27 calls (about 2,500 characters of arguments) where one 16-line script does it.** The picture was identical either way (largest difference 0 out of 255), so there is no gain in quality, only in effort.
* **"Grouped undo" means one undo step per call, not per job.** I ran it: a batch of three operations gives three undo steps. And there is no undo tool at all, so a machine running headless can never use it.
* **Many helpers at once is a weak point.** There is one Blender, one queue and one shared set of names. A long bake made a second caller wait 30 seconds and get a "timeout" error, and the request it had called a failure was carried out anyway afterwards.
* **Rendering the default way kills it on this machine** (no graphics card): the project's own test-suite lost 14 of 213 tests because Blender died during an EEVEE render. I reproduced the crash by hand.
* **It is not a hole by default, but it is not locked either.** It listens only on the machine itself, but it has no password and does not check who is calling: a web page you visit could make it do things (I ran a cross-site-style request and it was accepted). Without the Python tool it still lets a caller write files anywhere Blender can write.

**Verdict: skip it for our texture and modelling job.** Nothing it does is something we cannot already do with the official Blender Lab MCP and plain command-line scripts. Section 9 lists four small ideas worth borrowing. If the person later wants to rig and animate a character in a live Blender window, it is the one tool of this kind worth a supervised, closer look, and section 8 says what I would want first.

---

## 1. What it is

**One plain sentence:** a small program (the "tool server") that an AI assistant talks to, plus an add-on inside Blender, so that the assistant can say "add a node of this kind to this material" in a fixed, checked form instead of writing a Blender script.

**Concrete example first.** In the test I ran, the assistant-side was a short test program that sent these calls, one after another:

1. `material_create` with the name "mba_brick";
2. `shader_node_add` with the kind "ShaderNodeTexBrick" (Blender's own brick-pattern node);
3. `shader_node_set_input_value` nine times (three colours, then Scale, Mortar Size and so on);
4. `shader_node_connect_pins` to join the nodes;
5. `object_create` for a flat square, `material_assign_slot` to put the material on it;
6. `bake_setup_target_image` and `bake_run` to "photograph" the colour into a 512 x 512 picture, then `image_save_as`.

The picture came out right (a plain red brick pattern, section 4.3).

**The general rule.** Two parts work together:

* the **tool server**: a Node.js program (installed with `npm`) that tells the assistant which 216 tools exist and checks each call's arguments before passing it on;
* the **add-on** inside Blender: a small web server on the same machine (port 9877 unless you change it) that does the real work when a call arrives.

Every tool answers in the same shape: `ok`, `data`, `refs` (names to use in the next call), `nextSteps` and, on failure, an `errorCode` such as `MATERIAL_NOT_FOUND`.

Words used in this guide, each with one meaning:

* **tool**: one named command the assistant can call (for example `material_create`).
* **call**: one use of a tool.
* **tool server**: the Node.js program; **add-on**: the part inside Blender.
* **socket**: one input or output dot on a node (for example "Scale" on a Brick Texture node).
* **node setting**: a choice on a node that is not a socket (the Math node's operation, the Noise node's type, the stops of a Colour Ramp).
* **undo step**: one entry that Ctrl+Z removes.
* **bake**: turn the live node setup into a flat picture file.

---

## 2. Checking what the chat answer said

| What the chat said | Verdict | Evidence |
|---|---|---|
| "MCP Blender Agent is worth investigating for precise rigging and animation operations." | **True about the aim, not tested by me.** | 65 of the 216 tools are about rigging and animation (bones, armatures, actions, keyframes, NLA strips, constraints, shape keys) and more serve Unreal Engine 5 export. I did not use any of them. The project's own test-suite covers them and those tests passed here (section 4.9). |
| "It uses typed, validated tools rather than relying entirely on AI-generated Blender scripts." | **Partly true.** | Every tool has a declared list of arguments, and the server refuses wrong shapes before Blender sees them (ran: `roughness: 2.5` was refused with "Number must be less than or equal to 1"). But the key texture inputs are loose: the node kind is any text, the socket value is "a number, true/false, text or list", and a wrong value inside Blender comes back as a vague `INTERNAL_ERROR` (ran, section 4.4). |
| "...and supports grouped undo." | **Misleading.** | Each call ends with one "undo push", so each *call* is one undo step even if it changed many things inside. Calls are not grouped together: a `batch` of three operations gave three undo steps (ran, section 4.5). There is no undo or redo tool, so only a person pressing Ctrl+Z in a Blender window benefits. A comment in the project's own `helpers.py` says a failed call is not rolled back either. |
| "It is a much smaller project than the established MCP for Blender integration." | **True.** | 22 stars, 1 fork, 0 open issues, 121 npm downloads in the last month, one maintainer. The best-known Blender MCP (ahujasid) shows 31.7 thousand stars and 3.0 thousand forks. The official Blender Lab MCP is made by Blender Lab (part of the Blender project) and is a different program. |
| (implied) "It is a rigging tool, so it may help with texturing and modelling too." | **Not really for textures.** | 26 of the 216 tools touch materials, nodes, baking or UV unwrapping, and the gaps in section 4.5 stop them short of what our recipes need. |

**Which project is "MCP Blender Agent"?** I am fairly sure it is **PoBruno/mcp-blender-agent** on GitHub (npm package `@pobruno/blender-agent`). Its README says almost word for word what the chat said: "each operation becomes a typed tool: input validated... Composite mutations end with a single undo push", "no grouped undo" about other servers, "216 tools". The name in the chat is not invented. Other projects have similar names and similar goals (found in search, not tested): Rich-Siomporas/blender-agent (a harness built on the official Blender Lab MCP; its page returned "403 Forbidden", so I could not read it), carlosh7/blender-mcp (223 tools), RFingAdam/mcp-blender (218 tools), kleer001/blender-mcp, Mishaadevv/blender-mcp, and a "v3 rewrite" from StraySpark. If the person had a different one in mind, this guide does not cover it.

---

## 3. The real project

| Fact | What I found | Where it came from |
|---|---|---|
| Name | mcp-blender-agent (repository), `@pobruno/blender-agent` (npm), "BlenderAgent" (the add-on) | repository, npm |
| Author / maintainer | Bruno Gomes, handle "PoBruno" / "pobruno" (one person). Commits are from "pobruno", "dev" and the GitHub Copilot bot. The repository carries `CLAUDE.md` and Copilot instruction files, so it was most likely built with AI coding helpers (my inference). | `git log` of the clone; npm metadata |
| Official place | github.com/PoBruno/mcp-blender-agent ; npmjs.com/package/@pobruno/blender-agent | fetched |
| Licence | MIT, "Copyright (c) 2026 Bruno (PoBruno)". README: "Not affiliated with the Blender Foundation". | LICENSE file in the clone, npm |
| First commit | 8 June 2026 | `git log` |
| First release | npm 0.1.0 and 0.1.1, both 9 June 2026. There is no GitHub release and no tag. | npm registry |
| Latest change | 20 July 2026: five README edits by the Copilot bot and a merge. The last change to the code itself was 9 June 2026. It is now 19 October 2026, so about **three months with no commit** and four months with no code change. | `git log` |
| Version numbers disagree | npm 0.1.1; `package.json` in the repository 0.1.0; the add-on says 0.0.1; the server says 0.0.1. Small, but a sign of loose care. | read |
| Activity | 55 commits (49 of them on 8-9 June, 6 on 20 July), 22 stars, 1 fork, 0 watchers, 0 open issues. npm: 213 downloads on release day, 121 in the last 30 days. | repository page, issues page, npm downloads API |
| Blender versions | Says "4.2 LTS or later, 5.x recommended". The author's notes record a check on 5.1.2. **I ran it on 5.2.2** (it worked, section 4.2). | README; commit log; ran |
| Size | 216 tools, 218 routes inside Blender; about 14,000 lines of code; the published package is 739 KB unpacked and brings 96 npm packages (mostly the MCP library's own dependencies; I did not audit them). | ran; read |
| Documentation | README, an `install/` folder, a ".claude" folder of design notes. The README links to `.claude/docs/ARCHITECTURE.md`, which exists. There is no manual for texture work. | clone |

---

## 4. Tested here

### 4.1 Download, safety reading, install

* Cloned the repository (commit a45012e, 20 July 2026) into its own folder, and installed the **published npm package** `@pobruno/blender-agent@0.1.1` into a second empty folder with `npm install --ignore-scripts` (none of the 96 packages of the published package has an install script; I checked the lock file). For the repository's own test tools I ran `npm ci --ignore-scripts` too (162 more packages, 77 MB; I did not check those for install scripts).
* The add-on zip inside the npm package is the same code as the repository (the only difference is Windows line endings).
* **Read before running:** the add-on's web server (`server.py`), the helpers, the Python-exec tool, the node, material, bake, file, render and export handlers, the tool server's bridge and server tools. I searched all the code for network calls, subprocess use, deleting files and telemetry. Findings: **no calls to the internet and no telemetry** (the only web request is from the tool server to Blender on the same machine); no subprocess use in the add-on; the tool server starts Blender only from the `blender_launch` tool; the only file deletions are temporary picture tiles that the vision tools made themselves.
* I did **not** use the project's one-prompt installer. It tells an assistant to fetch instructions from the internet, edit your MCP settings, and insert a block into your `CLAUDE.md` or similar file. That is a lot of trust in one downloaded text (section 7).

### 4.2 Starting it headless, and does it load on 5.2.2

* **Ran.** The project only describes a Blender window as the normal way (the `blender_launch` tool opens a real window). Headless is what its test-suite does, so I did the same: `blender -b -t 2 --python-expr "import BlenderAgent; BlenderAgent.serve_blocking()"` with the port set to 19877 (our shared Blender server uses 9876; I stayed away from it).
* It was ready within 8 seconds on this busy machine (I did not time it more closely) and answered `server_status`: Blender "5.2.2 LTS".
* **Ran.** Also enabled it the "installed add-on" way (`addon_utils.enable("BlenderAgent")` with the add-on in a user-scripts folder inside my sandbox) and it started its server and answered. I did **not** click through Blender's Add-ons window (no screen here).
* **Ran.** It listens on 127.0.0.1 only (I read the socket list), not on the network.

### 4.3 The small texture job through the typed tools

**Ran** (`tests/t1_material_job.mjs`, which starts the real tool server and calls it exactly as an assistant would). 41 calls (27 for the job, 14 deliberate probes), about 1.2 seconds of call time in all, about 16-24 ms per ordinary call.

* Make material, add a Brick Texture node and a Texture Coordinate node, set 9 values, join them, put the material on a flat square, add an Emission node, bake the colour into a 512 x 512 picture, save it, save the .blend file: **all worked**.
* The picture: a clean red-brick pattern with grey mortar (file below). It has none of the wear, soot or outlines of our references, because I used only Blender's plain Brick node, on purpose.
* **Same job as one plain script** on the command line: 16 lines, 1.3 to 1.8 seconds including starting a fresh Blender each time. Picture identical to the typed one: **largest difference 0 out of 255**.
* **Same job in the official MCP** (`execute_blender_code_for_cli` on our `empty.blend`): one call, 0.23 seconds inside Blender, picture identical again (difference 0). The same call also set a Math operation, a Noise type, Colour Ramp stops and the brick offset, which the typed tools could not (section 4.5).
* Typed route: 27 calls, 2,492 characters of arguments, 4,520 characters of answers. Plain script: 1,193 characters. The machine time is small either way; the cost is the number of times the assistant has to stop and think.
* The 216 tool descriptions together are about 151,000 characters (roughly 38,000 tokens by a rough four-characters-per-token rule) that the assistant must hold in its head before it starts.

### 4.4 What the "typed and validated" layer caught, and what it did not

**Ran** (probes C1-C7 in the transcript).

| Mistake sent | What happened |
|---|---|
| Roughness 2.5 (allowed 0 to 1) | Refused by the tool server before Blender saw it: "Number must be less than or equal to 1 at roughness". **Good.** |
| Material that does not exist | `MATERIAL_NOT_FOUND`, clear message. **Good.** |
| Object that does not exist | `OBJECT_NOT_FOUND`, clear. **Good.** |
| Node kind "ShaderNodeNotARealNode" | `INVALID_INPUT`, "Node type ... undefined". **Good.** |
| Socket "Nope" | `INVALID_INPUT`, "socket(s) not found". **Good.** |
| Text "not a number" into a number socket | `INTERNAL_ERROR` with Blender's raw message. Refused, but not by the typed layer. |
| A single number into a colour socket | `INTERNAL_ERROR`, message cut off ("bpy_struct: item.attr = val:"). Refused, but unhelpful. |

So the checking is real for shapes and names, and weaker for the values that matter in a texture. Adding the same node twice does not fail and does not return the same node: it makes "Brick.001" (ran). A client has to read `refs` to learn the new name, or later calls quietly change the *old* node.

### 4.5 The gaps that matter for texture work

**Ran** (probes D1-D7 and the node-group test).

* **No node settings.** `shader_node_set_input_value` only sets sockets. Trying to set the Math node's `operation` or the Noise node's `noise_type` gives "socket 'operation' not found". Its own roadmap and catalogue promise noise, Voronoi and colour-ramp tools; the shipped version has only the five general node tools. The compositor has a set-property tool (`compositor_set_node_property`); the shader side was simply never given one.
* **No Colour Ramp stops.** I could add the node ("ShaderNodeValToRGB") and set its input, but there is no way to move or add stops or set their colours. Every one of our recipes uses ramps.
* **No node-group inputs and outputs.** `node_group_create` makes an *empty* group. I added Group Input and Group Output nodes and tried to join them to a Noise node: "socket(s) not found", because there is no tool that creates the named sockets. Our recipes are built as node groups with a `Vector` input and `Colour`, `Roughness`, `Metallic`, `Height` outputs, so they cannot be built through these tools. The geometry-node side is better (graph editing worked, I set the Grid node's size and applied the group to a plane) but also has no way to add your own group inputs.
* **A mistake in its own manual.** The project's workflow note E.3 ("Procedural via shader nodes") tells the assistant to add a node of kind `ShaderNodeColorRamp`. I checked in Blender 5.2.2: that kind does not exist (the real name is `ShaderNodeValToRGB`).
* **No orthographic camera.** `camera_create` has no "orthographic" choice, so our straight-down "photograph route" cannot be set up with it (the bake route did work, as above).
* **"Material recipes" are only numbers.** `parametric_material_recipe` returns plain values (colour, roughness, metallic) for six named materials such as "weathered_teak". It makes no procedural texture.
* **Destructive defaults (read, not run):** `material_create_pbr_from_textures` wipes the node tree of an existing material of the same name unless told not to; `material_create_procedural_grid` clears an existing material's nodes with no choice; `file_new` throws the open scene away without asking. It also loads image files as texture inputs, which our house rule forbids inside a recipe.

### 4.6 Undo: what "grouped" really means

**Ran**, on a second, throw-away instance with the Python tool switched on (the only way to press undo from outside).

* Four calls (create two materials, add two nodes): undo #1 removed the last node, #2 the first node, #3 the second material, #4 was refused (nothing left). **One undo step per call.**
* A call that does many things inside: `parametric_build` of the dining table (five objects and a material in one call). **One undo step** removed all five objects and the material together (ran on a third throw-away instance). That part is true and nice for a person in a Blender window.
* `batch` with three good operations then one bad: the three stayed (**not rolled back**) and undo needed three steps. So there is **no grouping across calls and no atomic batch**, although the project's own plan calls the batch "atomic".
* In headless use nobody presses Ctrl+Z and there is no undo tool, so for our job **grouped undo has no use**. Each helper should instead work on a fresh file and save versions.
* Cost of undo bookkeeping: none measurable. Call time stayed at about 17.7 ms with an empty scene, one 164 thousand-vertex mesh, and six of them (983 thousand vertices). Most of the 17 ms is the add-on checking its queue every 16 ms.

### 4.7 Many helpers at once

**Ran** (`tests/t3b_blocking_and_ghost.py`).

* One add-on = one Blender = one worker. A 2048 x 2048, 64-sample bake took 35.3 s (the machine was shared). A second caller who asked for "create material ghost_probe" half a second after it started **waited 30.0 s and received HTTP 504 `BLENDER_TIMEOUT`** ("main-thread job exceeded 30.0s").
* **The "failed" request still happened.** After the bake ended, `ghost_probe` existed. So a caller can be told "failed" and the thing is done later. For several helpers that is a trap.
* All names are shared by every caller. Two helpers using "Brick" or "shared_material" would overwrite each other (read from the code, not run). A material called "mba_brick" is created once and a second `material_create` returns `created: false`, which is handy, but the node tools are not that careful (section 4.4).
* What works: **one instance per helper**, each on its own port (`BLENDER_AGENT_PORT` for the add-on, `BLENDER_PORT` for the tool server). I ran three at once without trouble. Each takes about 300 MB. A plain command-line Blender script per helper needs none of this and is already isolated.

### 4.8 Speed

| Way of doing the same toy job | Time |
|---|---|
| Plain command-line script (fresh Blender each time) | 1.27 to 1.76 s |
| Official MCP, `execute_blender_code_for_cli` | 0.23 s inside Blender, plus its own start-up |
| Typed tools, Blender already running | 1.16 s for 41 calls, plus 27 separate assistant turns |

The machine time is the same order. The real cost of the typed route is the number of assistant turns, and the 38 thousand tokens (rough) of tool list. Keeping one Blender running avoids the start-up second, but our bakes are already about 20 seconds, so start-up does not matter.

### 4.9 The modelling side

**Ran** (`tests/t4_modelling.mjs`), all worked on 5.2.2:

* `object_create` (cube), `modifier_add` (Bevel, Subsurf with settings), `modifier_set_property` (this one takes any property of any modifier, so it is the most general tool in the set), `modifier_list`, `modifier_apply`, `mesh_shade_smooth`, `uv_smart_project`, `uv_validate_for_baking` (counts UV points outside 0..1: 0 here), `object_get_info`, `parametric_build` of a dining table (five named parts), `geo_node_apply_to_object`. A bad modifier kind gave a clear `INVALID_INPUT` listing the allowed kinds.
* Ready-made props are only four: beach chair, dining table, bar stool, a basic human. Fine as demos; not a kit for a coal mine.
* For building a scene from scripts, as the coal-mine scene was built, a script is shorter, can be kept as a file and can use everything in Blender; the typed tools cover the common 60 or so operations and nothing beyond.

**The project's own test-suite** (vitest, 213 tests; ran with a separate port and its temporary folder inside my sandbox): **197 passed, 14 failed, 2 skipped, 70 seconds.** The rigging, animation, armature, bone, modifier, material, bake, export and file tests passed on Blender 5.2.2 (the one exception is a rigging test in `sprint6` that failed only because Blender had already died earlier in that file). All 14 failures say "Cannot reach Blender": the Blender process **died during a render** (log line: "Couldn't open libEGL.so.1"), which took the rest of that test file with it. I reproduced it by hand: `render_set_engine BLENDER_EEVEE` then `render_render_still` gives "empty reply" and the process is gone. The same render with Cycles worked (256 x 256 in 0.8 s). The vision tools (snapshot, contact sheet, turntable) default to a render, so I would expect them to fail the same way here; I did not run them separately.

The suite talks to Blender's web port directly and **never goes through the tool server**, so it cannot catch tool-server mistakes (next section).

### 4.10 Bugs I found

1. **`exec_status` does not work.** The tool asks with GET, the add-on only answers POST: "No handler for GET /exec/status" (ran). The project's tests pass because they use POST.
2. **`server_status` reports the wrong thing.** It reads the setting `BLENDER_AGENT_ALLOW_EXEC`, but the Python tool is switched on by `BLENDER_AGENT_ALLOW_EXEC_PYTHON`. With the Python tool switched on and working, `server_status` still said `execPythonAllowed: false` (ran). The project's own decision note names the first setting, so the note and the code disagree.
3. **`blender_quit` says it quit and does not (headless).** It answered `{"quitting": true}`, but 12 seconds later Blender was still running and the requested file had not been saved: the delayed action relies on a Blender timer, and the headless loop does not run timers (ran). `server_shutdown` works. `addon_restart` uses the same mechanism (read, not run).
4. **Manual error:** `ShaderNodeColorRamp` (section 4.5).
5. **Timeouts that still do the work** (section 4.7).

### 4.11 Security probes (ran, on my own throw-away instances)

| Probe | Result |
|---|---|
| Is there a password or token? | **No.** None was sent and none was asked for. `/server/handlers` lists all 218 routes to anyone who asks. |
| A "simple" cross-site request as a web page could send it (`Content-Type: text/plain`, `Origin: http://evil.example`, `Host: evil.example`) | **Accepted and carried out** (it created a material). The add-on ignores `Origin`, `Host` and the content type. A page cannot read the reply, but the action happens. By the usual browser rules, ordinary JSON requests should be stopped, because the add-on answers the browser's pre-check with 501 (I reasoned this from the 501 reply; I did not test it in a real browser), so the risk is limited to this "simple request" kind. |
| Is the Python tool off by default? | **Yes.** `exec_python` answered `EXEC_PYTHON_DISABLED`. With `BLENDER_AGENT_ALLOW_EXEC_PYTHON=1` it ran arbitrary Python. |
| Write files to any place? | **Yes** (ran inside my sandbox only: `file_save_as` made new nested folders and a .blend file). The path is used as given: no folder limit. Same for `image_save_as`, `render_render_still`, the export tools and `blender_quit` with `saveAs` (read). |
| Quit the whole Blender by one request | The request is accepted without any check (section 4.10, number 3 explains why it did nothing headless). In a Blender window it would end the session. |
| Network listening | 127.0.0.1 only. Fixed port 9877 by default. |

---

## 5. Compared with what we already do

| | Official Blender Lab MCP + plain scripts (what we do) | MCP Blender Agent |
|---|---|---|
| Who makes it | Blender Lab (part of Blender). Licence GPL-3.0-or-later. Local copy: version 1.0.2, last commit 29 Sep 2026. Needs Blender 5.1 or newer. | One person. MIT. Quiet since July 2026. Blender 4.2+ (claimed). |
| Texture recipe (any node setting, ramps, node groups) | **Yes, everything**: one script call sets all of it (ran: Math operation, Noise type, ramp stops in one call). | **No** for settings, ramps and node-group sockets (ran). |
| Fitted description to picture | A recipe reads a JSON file and builds nodes in one go. | Would need hundreds of separate calls and still could not do all of it. |
| Many helpers at once | `execute_blender_code_for_cli` starts a fresh Blender per call: each helper is isolated. | One shared Blender per port; calls queue; 30-second timeouts; names shared. One instance per helper works but you start each by hand. |
| Headless, no graphics card | Yes (Cycles). | Yes, started by hand. Its own default renders (EEVEE, vision tools) kill it here. |
| Reproducible | A script file is the record. | The record is a list of calls; I got the identical picture, but you must keep the list yourself. |
| Undo | None in the add-on code (I found no undo handling). | One undo step per call; irrelevant without a window. |
| Safety | Arbitrary Python by design, with a "weak sandbox" that only blocks a few operations. Localhost socket. | No arbitrary Python by default, but file-writing and quit are open, no password, accepts cross-site "simple" requests. |
| Help finding names | `search_manual_docs`, `search_api_docs`, `get_python_api_docs`. | None. |
| Rigging and animation | Whatever you script. | **Its strength**: 65 dedicated tools, tests passing. |

---

## 6. Judged against our needs

1. **Pixel-accurate matching from a compact fitted description.** No help. The matching depends on the recipe reading a description and exposing every setting (ramps, noise types, group inputs). The typed tools cannot reach those. Our `description.json` plus a Python recipe is already a better "typed description" than a list of tool calls.
2. **Many variants and larger areas.** No help; the work is the same bake run again with a new description. A plain script loop does this; calling a tool server 27 times per variant would be slower to steer.
3. **Lessons that transfer to other surfaces.** Almost none (section 9 has the few).
4. **Running headless and scripted without a graphics card.** Possible, as shown, but not its normal mode, and its default render path crashes here. Plain `blender -b` scripts are simpler and safer.
5. **Modelling (secondary).** It works and has some pleasant one-call helpers (modifier settings by dictionary, UV check, bevel), but scripts cover the same ground, and for the coal-mine style of job a script file is the better record.

**Typed or checked editing for a job built from recipes and many parallel helpers:** the checking that would help us is checking *the recipe's description* before Blender starts (a wrong number found in a second instead of after a 20-second bake). We can do that ourselves with a small schema check. The tool server's checking happens one call at a time and cannot see a whole recipe.

---

## 7. Security: what it can do to the machine, and what I would want before trusting it

**What the add-on can do, as shipped** (read, and the starred items ran):

* run a web server on 127.0.0.1:9877 with no password*;
* accept requests from any web page open in a browser on the same machine, as long as they are "simple" requests*;
* create, change and delete anything inside the open Blender file*;
* write .blend, picture and export files to any path Blender can write*;
* open, link, append and import any file Blender can read (`file_open`, `file_append_data`, `import_*`, `library_link`): opening a booby-trapped .blend could run its embedded scripts if Blender's "auto-run" is on, and the project does not start Blender with `--disable-autoexec` (read);
* throw the whole session away (`file_new`) or quit Blender (`blender_quit`)*;
* with `BLENDER_AGENT_ALLOW_EXEC_PYTHON=1`: run any Python, which means anything the user can do*;
* the `blender_launch` tool starts Blender from `BLENDER_BIN` or standard folders. If the add-on is not installed in Blender, it adds the *parent folder of the tool server's working folder* to Python's search path and imports `BlenderAgent` from there, so a folder with that name placed there would be run (read, not run; low risk but worth knowing).

**What it does not do** (read): no calls to the internet, no telemetry, no running of other programs from the add-on, no hidden listening port.

**Supply chain.** The install prompt uses `npx -y @pobruno/blender-agent@latest`, which fetches whatever version is newest every time the assistant starts. The package has one maintainer and no provenance statement (the commit "provenance off in publishConfig" says so). The installer also edits your assistant's settings and instruction files. I would not use it that way.

**What I would want before trusting it:**

1. Install a **fixed version** (for example `npm install @pobruno/blender-agent@0.1.1 --ignore-scripts`) and read the diff before upgrading; do not use `@latest` or the one-prompt installer.
2. Run the add-on in a **separate user account or container**, on a random port, never on a machine with a browser logged in to anything important, **or** first add a check of `Host` and `Origin` and a secret header (about ten lines in `server.py`).
3. Keep `exec_python` **off**.
4. A **folder allow-list** for every path argument, and a read-only mode.
5. Real tests of the tool-server layer (today none exist) and fixes for the five bugs in section 4.10.
6. A **long-term sign of care**: releases, answered issues, a second maintainer. Today: none.
7. An independent look at the 96 npm dependencies (I did not do this).

For comparison, the official Blender Lab MCP and the ahujasid server are open to arbitrary Python by design and also have no password. So this is not worse in kind. It is only better in that arbitrary Python is off until you switch it on.

---

## 8. Verdict

* **Skip it** for the texture job and for our scripted modelling. It does not reach the node settings, ramps and group inputs our recipes need, it adds many steps for the same picture, it shares one worker between helpers, and its default rendering crashes without a graphics card.
* **Borrow four ideas** (section 9). They cost us nothing.
* **Not for now, but the one fair use:** rigging and animation for a game engine, in a live Blender window, by one person at a time, with a fixed version, on a machine you can afford to lose. I did not test that use. The project's own tests for it passed on 5.2.2.

---

## 9. What we could take into the job

1. **A stable answer shape and error codes.** Every tool answers `ok / data / refs / nextSteps / errorCode`, with a fixed list of codes (`OBJECT_NOT_FOUND`, `INVALID_INPUT`, ...). Our scripts and recipes could write the same shape into `bake.json`, so a helper or a later step can read "what went wrong" without parsing text.
2. **Check the description before launching Blender.** Add a small schema check for each recipe's parameters (types and ranges), the way the tool server refuses `roughness: 2.5`. We already have `description_audit.py` for size; a "values in range" check would save 20-second wasted bakes.
3. **A "ready to bake?" check for objects.** `uv_validate_for_baking` counts UV points outside 0..1 and makes sure a UV layer exists. Flat tiles do not need it, but the transfer step (textures on real objects such as the coal-mine buildings) will. This is about 20 lines in plain Blender Python to re-create.
4. **Version-tolerant socket names.** Their Principled helper tries "Emission Color" then "Emission", and "Specular IOR Level" then "Specular", so one call works across Blender versions. Our recipes should do the same wherever socket names changed between 4.x and 5.x.
5. **Handy one-call facts** for later reference: the name list of the human-proportion and furniture tables in `BlenderAgent/library/anatomy/proportions.py` (only worth reading if we ever need human-scale numbers).
6. **Lessons about the shape of the problem, not code:** (a) a tool list that only sets sockets is not enough for texture work: the settings, ramp stops and group interfaces are the heart of a recipe; (b) one Blender worker needs timeouts that are honest (do not run a "failed" request later); (c) "one undo step per recipe step" is a useful idea if a person ever steps through a recipe by hand in a Blender window.

**No algorithms, file formats or new nodes** came out of this tool: it contains no texture algorithms of its own (its material helper returns numbers, and the brick, noise and ramp nodes are Blender's).

**If the person wants the typed route anyway**, the smallest repair is three new tools: `shader_node_set_property` (copy `compositor_set_node_property`), `shader_node_set_ramp_stops`, and `node_group_add_socket`, about 50 lines of Python each. I have not written or tested them. For our job, the official MCP's one-call script does all of this already.

---

## 10. Not tested (and why)

* **Rigging, animation, armatures, NLA, export (FBX/glTF/USD):** out of scope; only seen through the project's own passing tests.
* **Anything that needs a window:** `blender_launch`, viewport screenshots, `vision_snapshot`, turntables, the Add-ons-window install. No screen or graphics card here. The vision tools probably crash like EEVEE did (not run).
* **The one-prompt installer:** deliberately not used (section 7).
* **Windows and macOS:** Linux only.
* **Blender 4.2, 4.4, 5.0, 5.1:** only 5.2.2.
* **Two helpers writing to the same name:** read from the code, not run (the blocking and timeout test was run).
* **Other "Blender agent" projects** (Rich-Siomporas, carlosh7, RFingAdam, kleer001, StraySpark): seen in search results only; one page returned 403.
* **The npm dependencies:** counted, not audited.
* **My three suggested new tools:** not written.
* **Whether "Mixar" exists:** this belongs to the Ucupaint guide; a quick search of mine also found no product called "Mixar" (it found Mixos, a browser texture painter, and several layered-texture add-ons).

---

## 11. Where the test files are

Everything is in `proc-work/third-party/mcp_blender_agent/`:

* `repo_clone/` the cloned repository (and its installed test tools); `npm_install/` the published package; `addon_extract/` the add-on zip unpacked; `blender_user_scripts/` the add-on in a user-scripts folder for the "installed add-on" test.
* `tests/` my scripts: `mcpclient.mjs` (starts the real tool server and calls a tool), `t0_list_tools.mjs`, `t1_material_job.mjs`, `t3_concurrency.py` (first version; the useful one is `t3b_blocking_and_ghost.py`), `t4_modelling.mjs`, `t5_enable_as_addon.py`, `t_exec_status_tool.mjs`, `plain_brick.py` (the same job as one plain script).
* `out/t1/` the baked picture `mba_brick_colour.png`, the Cycles render, the saved .blend and the full call-by-call transcript `t1_transcript.json`; `out/plain/` and `out/official/` the same picture made the other two ways; `out/tool_list.json` all 216 tool definitions.
* `logs/` console output, including the full test-suite run `vitest_full.log`. `notes/measurements_copied_from_console.txt` has the numbers quoted above.

## 12. How to repeat the tests

1. `npm install @pobruno/blender-agent@0.1.1 --ignore-scripts` in an empty folder; unpack `assets/BlenderAgent.zip`.
2. Start the add-on: `BLENDER_AGENT_PORT=19877 blender -b -t 2 --python-expr "import sys; sys.path.insert(0, '<folder with BlenderAgent>'); import BlenderAgent; BlenderAgent.serve_blocking()"`.
3. Run `node tests/t1_material_job.mjs <output folder>` (set the folder names at the top of `mcpclient.mjs`). To enable the Python tool for the undo test, start a second instance with `BLENDER_AGENT_ALLOW_EXEC_PYTHON=1` on another port.
4. Stop with a POST to `/server/shutdown` (not `blender_quit`, which does nothing headless).

---

## Sources

| Title | URL | Date | What it gave me |
|---|---|---|---|
| mcp-blender-agent (GitHub repository page) | https://github.com/PoBruno/mcp-blender-agent | fetched 19 Oct 2026 | Description, licence (MIT), 22 stars, 1 fork, 0 watchers, 55 commits, README (typed tools, "single undo push", ~216 tools, Blender 4.2+), install prompt |
| mcp-blender-agent, cloned source (commit a45012e, 20 Jul 2026) | https://github.com/PoBruno/mcp-blender-agent (cloned) | commits 8 Jun to 20 Jul 2026 | All code reading, `git log` dates and authors, ADR notes, ROADMAP, install and skill files, the project's test-suite |
| mcp-blender-agent issues | https://github.com/PoBruno/mcp-blender-agent/issues | fetched 19 Oct 2026 | 0 open issues |
| @pobruno/blender-agent on npm (registry data) | https://www.npmjs.com/package/@pobruno/blender-agent (read through registry.npmjs.org) | versions 0.1.0 and 0.1.1, 9 Jun 2026 | Version, publish dates, MIT, maintainer, dependencies (MCP SDK 1.32.1, zod), unpacked size 739 KB |
| npm download counts | https://api.npmjs.org/downloads/point/last-month/@pobruno/blender-agent | 19 Oct 2026 | 121 downloads in 30 days; 213 on 9 Jun 2026 |
| Blender MCP search results (several projects) | web search "MCP Blender Agent typed validated tools grouped undo rigging animation" | 19 Oct 2026 | Which project the name points to; names of similar projects (carlosh7, RFingAdam, Mishaadevv, kleer001, StraySpark v3 blog https://www.strayspark.studio/blog/blender-mcp-server-v3-blender-5x-rewrite-404-tools) |
| Rich-Siomporas/blender-agent (Blender Projects) | https://projects.blender.org/Rich-Siomporas/blender-agent | search snippet only; page gave "403 Forbidden" | Existence only ("agent harness built on lab/blender_mcp") |
| ahujasid Blender MCP (GitHub page) | https://github.com/ahujasid/blender-mcp | fetched 19 Oct 2026 | 31.7k stars, 3.0k forks, MIT, 9 tools incl. `execute_blender_code`, localhost port 9876, README warning "no authentication or encryption" |
| Blender Lab blender_mcp (the official one) | https://projects.blender.org/lab/blender_mcp (page "403 Forbidden"); local copy at `/home/user/work/blender-mcp/src` | local copy HEAD 29 Sep 2026 | Version 1.0.2, GPL-3.0-or-later, Blender 5.1+, `weak_sandbox.py` ("more guidance than a sandbox"), no undo handling found, localhost socket |
| "Mixar" search | web search "Mixar Blender texture layer editor" | 19 Oct 2026 | No product called Mixar found (the Ucupaint guide has the other helper's findings) |
