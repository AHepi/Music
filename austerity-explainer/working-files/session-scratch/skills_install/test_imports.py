"""Import test for the installed Scenario Blender skills (run inside Blender, headless)."""
import importlib, os, sys, traceback

sys.dont_write_bytecode = True          # keep __pycache__ out of the installed skills
SKILLS = "/home/user/Music/.claude/skills"
SCRIPT_DIRS = [os.path.join(SKILLS, d, "scripts") for d in sorted(os.listdir(SKILLS))
               if os.path.isdir(os.path.join(SKILLS, d, "scripts"))]
EXPERT = os.path.join(SKILLS, "scenario-blender-expert", "scripts")
MODULES = ["bx_audit", "bx_review", "bx_gui", "bx_materials", "bx_uvbake", "bx_gn", "bx_light",
           "bx_export", "bx_previs"]
failures, notes = [], []

print("skills found:", [os.path.basename(os.path.dirname(d)) for d in SCRIPT_DIRS])
for d in SCRIPT_DIRS:                    # the way the docstrings say: sys.path.append("<skill>/scripts")
    if d not in sys.path:
        sys.path.append(d)

mods = {}
for name in MODULES:
    try:
        m = importlib.import_module(name)
        mods[name] = m
        where = os.path.dirname(os.path.abspath(m.__file__))
        expect = os.path.join(SKILLS, {"bx_audit": "scenario-blender-expert", "bx_review": "scenario-blender-expert",
            "bx_gui": "scenario-blender-expert", "bx_materials": "scenario-blender-texturing-shading",
            "bx_uvbake": "scenario-blender-uv-baking", "bx_gn": "scenario-blender-geometry-nodes",
            "bx_light": "scenario-blender-lighting-rendering", "bx_export": "scenario-blender-export",
            "bx_previs": "scenario-blender-previs-storyboard"}[name], "scripts")
        assert where == expect, f"loaded from {where}, expected {expect}"
        print(f"OK {name}  ({getattr(m, '__version__', '?')})")
    except Exception as e:
        if name == "bx_gui":
            notes.append(f"bx_gui did not import headless (meant for a live window): {e!r}")
            print(f"NOTE {name}: {e!r}")
        else:
            failures.append(name)
            print(f"ERROR {name}: {e!r}")
            traceback.print_exc()

# ---- cross-links: the scripts must find the expert skill's scripts by their own location
def forget_expert():
    while EXPERT in sys.path:
        sys.path.remove(EXPERT)
    for n in ("bx_review", "bx_audit"):
        sys.modules.pop(n, None)

try:
    forget_expert()
    R = mods["bx_uvbake"]._review_helpers()
    assert EXPERT in sys.path and os.path.dirname(os.path.abspath(R.__file__)) == EXPERT
    for attr in ("_world_bbox", "_sample_points", "_extent", "_persp_distance", "_look_at", "_tile", "VIEW_DIRS", "PERSPECTIVE"):
        assert hasattr(R, attr), "bx_review lacks " + attr
    print("OK link bx_uvbake -> scenario-blender-expert/scripts/bx_review.py (all helper names present)")
except Exception as e:
    failures.append("link uvbake"); print("ERROR link uvbake:", repr(e))

try:
    forget_expert()
    M = mods["bx_materials"]
    assert os.path.isfile(os.path.join(M._EXPERT, "bx_review.py")) and os.path.normpath(M._EXPERT) == EXPERT
    import bx_review as R2   # bx_materials put the expert folder on sys.path at import time (re-add if forgotten)
    print("OK link bx_materials -> scenario-blender-expert/scripts/bx_review.py")
except ModuleNotFoundError:
    sys.path.append(M._EXPERT)
    import bx_review as R2
    print("OK link bx_materials -> expert scripts (path computed by bx_materials._EXPERT is right)")
except Exception as e:
    failures.append("link materials"); print("ERROR link materials:", repr(e))

try:
    forget_expert()
    X = mods["bx_export"]
    p = os.path.join(X.SKILLS, "scenario-blender-expert", "scripts")
    assert os.path.normpath(X.SKILLS) == SKILLS and os.path.isfile(os.path.join(p, "bx_audit.py"))
    sys.path.append(p)
    import bx_audit as A2     # what bx_export.batch() does
    assert callable(A2.deliverable)
    print("OK link bx_export -> scenario-blender-expert/scripts/bx_audit.py (deliverable found)")
except Exception as e:
    failures.append("link export"); print("ERROR link export:", repr(e))

try:
    if EXPERT not in sys.path:
        sys.path.append(EXPERT)
    sys.modules.pop("bx_review", None)
    import bx_review as R3    # what bx_previs.animatic() does
    assert callable(R3.playblast)
    print("OK link bx_previs.animatic -> bx_review.playblast found")
except Exception as e:
    failures.append("link previs"); print("ERROR link previs:", repr(e))

for n in notes:
    print("NOTE:", n)
print("RESULT:", "ALL OK" if not failures else "FAILURES " + ", ".join(failures))
if failures:
    sys.exit(1)
