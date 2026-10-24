import sys, json
D = sys.argv[1]
checks = [
 # (label, file, old)
 ("FR1 npx sentence", "SKILL.md", "If a sibling skill named here is missing from your available skills, ask the user\nto install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool\nschemas and flag the gap."),
 ("FR2 exec channel", "SKILL.md", "(execution channel, review loop, 5.2 API changes)"),
 ("FR3 preview step8", "SKILL.md", "`M.preview` (EEVEE and Cycles, studio, backlit, roughness),"),
 ("FR4 default cycles finals", "SKILL.md", "Cycles finals, EEVEE side by side"),
 ("FR5 GUI brushes", "SKILL.md", "GUI: brushes are assets"),
 ("FR6 factory settings", "references/expert-notes.md", "Load Factory Settings when lost"),
 # my candidates
 ("N1 toolkit line", "SKILL.md", "import bx_materials as M`."),
 ("N2 critique render first", "references/critique.md", "EEVEE and Cycles), open the sheet,"),
 ("N3 visual gate", "SKILL.md", "Visual: `M.preview` EEVEE vs Cycles nearly identical;"),
 ("N4 preview default", "scripts/bx_materials.py", 'def preview(target, out_dir, engines=("BLENDER_EEVEE", "CYCLES"), rigs=("studio", "backlit"),'),
 ("N5 mkdtemp P11", "references/procedures.md", "out = tempfile.mkdtemp()"),
 ("N6 mkdtemp P13", "references/procedures.md", "sheet = M.preview(mat, tempfile.mkdtemp(), engines=(\"BLENDER_EEVEE\",), rigs=(\"studio\",), res=160, samples=8)"),
 ("N7 step4 gate", "SKILL.md", "`M.preview(objs, out, rigs=(\"studio\", \"roughness\"))`: effects follow form and water paths,"),
 ("N8 P10 gui header", "references/procedures.md", "## P10. Texture painting with real brushes (live GUI session)"),
 ("N9 P9 header", "references/procedures.md", "## P9. Anisotropic hair or brushed metal (Cycles only)"),
 ("N10 P15 header", "references/procedures.md", "## P15. Global clay switch driven by one property (Kaspar, Snow finale)"),
 ("N11 gpu block", "scripts/bx_materials.py", '            prefs.compute_device_type = "METAL" if sys.platform == "darwin" else "CUDA"'),
 ("N12 value_report def", "scripts/bx_materials.py", 'def value_report(objs, res=256, views=("front", "threequarter"), engine="CYCLES", out_dir=None):'),
 ("N13 critique sect6", "references/critique.md", "- EEVEE and Cycles nearly identical side by side (Kaspar)."),
]
for label, f, old in checks:
    t = open(f"{D}/{f}", encoding="utf-8").read()
    print(f"{t.count(old)}  {label}  [{f}]")
