import sys, json
B = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/downloads/scenario-skills/skills/dcc/blender/scenario-blender-previs-storyboard/"
S = B + "SKILL.md"; PR = B + "references/procedures.md"; SRC = B + "references/sources.md"; PY = B + "scripts/bx_previs.py"
cases = [
 ("first: self-install", S, "If a sibling skill named here is missing from\nyour available skills, ask the user to install it\n(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and\nflag the gap."),
 ("first: P21 heading", PR, "## P21. Storyboarding app template (replaces the open file, run last)"),
 ("first: blockout", S, "rebuild it with scenario-blender-blockout,"),
 ("first: strokes SKILL", S, "Strokes: scenario-blender-grease-pencil."),
 ("first: anim/rig", S, "layout: scenario-blender-animation. Real rigs: scenario-blender-rigging."),
 ("first: strokes proc", PR, "Strokes: scenario-blender-grease-pencil;"),
 ("first: rigging proc", PR, "Full rigging: scenario-blender-rigging."),
 ("first: py docstring", PY, "The drawing itself is the scenario-blender-grease-pencil skill's job."),
 ("mine: required background", S, "**REQUIRED BACKGROUND:** scenario-blender-expert (execution channel, review loop, 5.2 API changes)."),
 ("mine: test command", PR, "blender --background --factory-startup --python-exit-code 1 --python tests/code/blender-previs-storyboard/<test>.py"),
 ("mine: app-template cli", PR, "line: `blender --app-template Storyboarding`."),
 ("mine: OUT placeholder", PR, "# any writable folder"),
 ("mine: sources guard", SRC, "Seven videos, distilled in"),
 ("mine: animatic guard", PY, "    ed = bpy.data.scenes.get(edit_name or sc.name.replace(\"_blend\", \"_edit\")) or \\\n        bpy.data.scenes.new(edit_name or sc.name.replace(\"_blend\", \"_edit\"))\n"),
]
for label, path, old in cases:
    print(f"{path.split('previs-storyboard/')[1]:28s} count={open(path).read().count(old)}  {label}")
