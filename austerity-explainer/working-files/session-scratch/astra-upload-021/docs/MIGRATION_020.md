# Migration and exact scope

This release was built from the exact recovered 0.1.9 installer, SHA-256 `fa70b5a62547e05b7f2f26307f7b6fc069be3573032ae4e513c1b54466c5117f`. That installer is retained unchanged in the companion evidence bundle. The recovered original UI and preview code remain; 0.2.0 adds actual runtime modules and operators. Earlier 0.1.9 guidance-only release notes are historical, not the current runtime claim.

No invisible migration of old scenes occurs. Existing 0.1.9 previews continue using their prior workflow; restore or keep an active preview before instrumenting the same object with a new surface transaction. Existing terrain, moss, bridge, fabric and palette recipes are not automatically discovered by names. New operations require explicit receiver IDs and masks. Objects with unsupported modifiers or active transactions are rejected.

Supported and executed: Blender 5.1.2 on the isolated Linux runtime; registration/unregistration, operator invocation, JSON contracts, retained data and native effects after save/reopen. The extension declares Blender 5.1.x. Full graphical install clicks, other OSes, Blender 4.x/5.0/5.2+, arbitrary shader graphs, library overrides, animation and broad third-party add-on interactions are not qualified.

The terrain and plank generator uses ordinary retained meshes with explicit regeneration. Native candidate scatter and the earlier roof/stone components use live Geometry Nodes. The courtyard terrain, continuous moss body, lower-rock moss and curved bridge remain explicit scene adapters, supplied with provenance. This is partial mechanism consolidation with actual courtyard use, not a claim that every historical scene recipe is now a general-purpose tool.

Rejected sky, Toon, palette and early moss-visibility pilots are excluded from successful default presets. They inform failure tests only. Moss ecological masks, real body geometry and visible moss are different claims; the UI never labels a numeric mask pass as visual acceptance.

Accepted background palette code is preserved as a narrow reference. It is not used to recolor arbitrary scenes. Only the explicitly qualified fabric overlay and pigment/material primitives are exposed as selected-object runtime operations.
