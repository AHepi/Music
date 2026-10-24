# 0.2.1: creation and surface-detail rollback

## What changed

In 0.2.0, a deliberately injected selection error after a successful plank build made the registered operator return CANCELLED while leaving its 2 objects, 1 mesh, 1 collection and 7 materials. A preflight rejection left no new data. This was a controlled robustness test, not an observed spontaneous user failure.

Six creation operators now keep their transaction open through selection, audit and reporting: landscape Create and Rebuild, varied planks, native candidate scatter, ceramic roof and chiseled stone. If one of those steps raises, the wrapper removes the IDs allocated during explicit creator/report calls, restores prior selection and active object, and restores tracked landscape source/prior-generation visibility and flags. The error remains an error; it is not silently reported as success.

The same independent review then demonstrated a surface-detail report failure returning CANCELLED with its completed private-mesh/material transaction still active. The material-specific detail operator now restores through its retained source handle before removing newly captured IDs if its audit/reporting step fails. Both failure before report creation and failure after Text creation are covered. This is a narrow additional correction to that observed path.

Identity, not object names, determines removal. Existing meshes, materials, source banks and older generations are not removed. An unrelated ID allocated later by the failing UI callback is outside the captured allocation window and is preserved. No global orphan purge, scene reset, persistent hook, automatic save or user preference change is introduced.

## Checks before this package was frozen

An isolated Blender 5.1.2 official extension installation loaded the real `bl_ext.rollback.astra_painted_workbench` namespace. Registered operators passed the exact late-selection fault, partial-selection failure, invalid-input neighbor, source/rebuild flag rollback, late report failure, surface-detail report-before/report-after rollback, shared source DATA/OBJECT bindings, appended roof/stone dependencies, native scatter, name collisions, unrelated late ID preservation and normal creation/restore checks. The test compared exact live ID identity sets plus original object geometry/material/visibility, selection, active object, tracked flags and report selection. These are technical checks, not an artistic-quality verdict.

The delivered archive is additionally subject to independent frozen-candidate installation and save/reopen checks. Their final results accompany the release, rather than being written back into this frozen installer.

## Boundaries

- This covers six creation operators plus material-specific detail, not a universal Blender transaction layer.
- Pigment/textile application, preview, restore and configuration wrappers are unchanged. Existing core source-retention behavior is preserved; this maintenance change does not newly certify every error path in those wrappers.
- Existing core API and vendor geometry-generation functions are unchanged. Direct API callers retain their existing API-level contracts; these wrappers extend only the seven named registered operators.
- GUI Undo/Redo remains unqualified here: no usable graphical display was available, and background execution is not an interactive Undo witness.
- Arbitrary third-party callbacks that mutate existing user data inside a captured factory are outside the tested contract. The wrappers are synchronous and track their named retained objects and allocation windows.
- Human review of actual hero/near renders remains required. Existing source/scale/mask restrictions still apply.

The saved outputs remain ordinary Blender data; the wrapper is needed to run the operation, not to display its saved result.
