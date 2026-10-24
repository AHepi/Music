export const meta = {
  name: 'assess-worldsculpt',
  description: 'Find out what WorldSculpt needs and makes, and whether it would help the explainer films',
  phases: [{ title: 'Research', detail: 'the tool itself; how it would fit this pipeline and what else would' }],
}
const TOOL = {
  type: 'object',
  properties: {
    what_it_does: { type: 'string' },
    inputs_needed: { type: 'string' },
    outputs: { type: 'string' },
    code_and_weights_released: { type: 'string' },
    licence: { type: 'string' },
    hardware: { type: 'string' },
    hosted_anywhere: { type: 'string' },
    maturity_and_caveats: { type: 'string' },
    sources: { type: 'array', items: { type: 'string' } },
  },
  required: ['what_it_does', 'inputs_needed', 'outputs', 'code_and_weights_released', 'licence', 'hardware', 'hosted_anywhere', 'maturity_and_caveats', 'sources'],
}
const FIT = {
  type: 'object',
  properties: {
    machine_can_run_it: { type: 'string' },
    fit_with_pipeline: { type: 'string' },
    where_it_could_help: { type: 'string' },
    better_alternatives: { type: 'array', items: { type: 'object', properties: {
      name: { type: 'string' }, what: { type: 'string' }, how_to_use_here: { type: 'string' }, cost: { type: 'string' }, source: { type: 'string' } }, required: ['name', 'what', 'how_to_use_here'] } },
    verdict: { type: 'string' },
  },
  required: ['machine_can_run_it', 'fit_with_pipeline', 'where_it_could_help', 'better_alternatives', 'verdict'],
}
phase('Research')
const [tool, fit] = await parallel([
  () => agent(`Research the research project "WorldSculpt" (project page https://alaya-lab.github.io/WorldSculpt/, Alaya Lab, University of Tokyo; paper arXiv 2609.05416; code github.com/AlayaLab/WorldSculpt; weights huggingface.co/AlayaLab/WorldSculpt). Read the project page, the arXiv abstract page, the GitHub README (and LICENSE file) and the Hugging Face model card. Use WebFetch and WebSearch (load them with ToolSearch "select:WebFetch,WebSearch"). Do not download or run anything.
Report plainly and only what the sources say: what it does; exactly what it needs as input (posed multi-view images? instance masks? 3D boxes? how many views? can it start from one painting?); what it outputs (mesh formats, textures?); whether the code and weights are actually released and usable today or "coming soon"; the licence of code and weights (commercial use allowed?); hardware (GPU type and memory, run time per scene); whether any hosted service (fal.ai, Replicate, Hugging Face Spaces) runs it; caveats. Quote short key sentences and list the URLs you used. If a page fails to load, say so rather than guessing.`, { label: 'what WorldSculpt is', phase: 'Research', schema: TOOL, effort: 'medium' }),
  () => agent(`Judge whether the research tool WorldSculpt (https://alaya-lab.github.io/WorldSculpt/ : turns posed RGB views of a complex 3D scene, with per-object instance masks and 3D bounding boxes, into separate complete 3D meshes, one per object; built on a single-object 3D generator, Pixal3D; can work from rendered views of 3D Gaussian-splat worlds such as World Labs' Marble) would help make the user's narrated explainer films, and what would help more. Use WebFetch/WebSearch (load with ToolSearch "select:WebFetch,WebSearch") for facts; do not download, install or run models, and spend nothing.
The films and how they are made now (read /home/user/Music/austerity-explainer/project-notes/Austerity explainer - project story.md, sections "How the pieces fit" and log entries 19 to 21, for detail):
- Tall phone videos (1080x1920), 4-5 minutes a chapter, drawn by three.js in a headless Chromium with software graphics (SwiftShader) on a 4-processor cloud machine with NO graphics card; filmed at about 3 to 15 seconds a frame.
- Pictures: single paintings made with fal (Flux), each turned into a "painted room with depth" using a fal depth map (Depth Anything v2), so the camera can move a little way in; cut-out paper figures; 3D models built by Python scripts in Blender (headless, Blender 5.2.2, with the official Blender MCP server) and saved as .glb (two factories ~34,000 triangles each, a town ~63,000, a desk, props), loaded in three.js.
- The user's earlier feedback: wanted much higher-quality 3D models that fill the frame; painted rooms break when the camera moves far; things must not clip through each other; camera stays still unless a move is essential (max 3 moves a shot).
- Budget: fal allowed up to US$10 for pictures (about US$1.16 used on chapter 2); every spend must be confirmed with the user first. No other paid compute is set up (a RunPod connector exists but is not signed in).
Check: can this machine run WorldSculpt at all (look at /home/user/Music for nothing; just check nvidia-smi and free memory with Bash: 'nvidia-smi; free -g; nproc')? Would its inputs be available from this pipeline (we have single 2D paintings, not posed multi-view captures with masks and boxes)? Where could it help (for example breaking a generated 3D world into separate objects that can be moved, lit and kept from clipping)? Then name 2 to 4 concrete alternatives that fit better today, preferably runnable through fal or on this CPU-only machine (for example single-image-to-3D models on fal such as Hunyuan3D, TRELLIS or similar; 3D world generators; gaussian-splat viewers in three.js), with what each would do here, approximate cost per use from the provider's pricing page, and a source URL. Be concrete and honest about uncertainty.`, { label: 'fit with the films', phase: 'Research', schema: FIT, effort: 'medium' }),
])
return { tool, fit }
