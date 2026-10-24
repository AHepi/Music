# Astra Painted Workbench 0.2.0

CURRENT WORKING SNAPSHOT, returned at the user’s request on 2026-10-18 at 21:32 UTC. Runtime tests passed within the declared scope; final artistic/courtyard review is pending. Later work will use a separate archive.

Actual runtime integration into the recovered 0.1.9 add-on. Blender 5.1.x; qualified in an isolated Blender 5.1.2 process. The original preview workflow is retained.

Install the supplied extension ZIP using Blender Preferences → Get Extensions → Install from Disk. No preferences or persistent installation were changed by the tests. Open 3D View → Sidebar → Astra Paint → Transferable Scene Tools.

Start with a copy of your scene. Choose an explicit static receiving surface, make the starter JSON, and review its traffic and support masks before building. The starter cannot infer a hall, pond, bridge, foundation, or safe walking area. Generated landscape meshes use explicit Create/Rebuild; the separate candidate-scatter tool builds live Geometry Nodes. Both retain original source IDs and include checks and restore controls.

- [Runtime guide and supported API](docs/RUNTIME_020.md)
- [Scope, migration and exclusions](docs/MIGRATION_020.md)
- [Concrete lessons enforced in code](docs/LESSON_ENFORCEMENT_020.md)
- [Qualification evidence](docs/QUALIFICATION_020.md)
- JSON schemas and examples are in `data/`.

Human review of hero and near renders is still required. A numeric or registration pass does not certify visual quality, ecology, structural safety, or arbitrary scenes.
