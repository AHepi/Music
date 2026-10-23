export const meta = {
  name: 'village-without-the-plugin',
  description: 'Control test: Sonnet at maximum effort builds the same village with Blender through its MCP connection only: no plugin, no rented cards, no reference pictures, no other files',
  phases: [{ title: 'Build', detail: 'one isolated Sonnet run' }],
}

const F = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-control'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'

phase('Build')
const report = await agent(`A person asked, in these words: "Now build a village in the forest. Needs unkept dirt roads like they're been driven down by horse and carriage, an empty stable, a few cottages, some scattered mediaeval props."
Build it in Blender 5.2, working through Blender's MCP tools: load them with ToolSearch (for example "select:mcp__blender__execute_blender_code,mcp__blender__get_objects_summary", and search "blender" for the others) and use them for all Blender work. A Blender instance is already running and connected to those tools. It runs in background mode (no window) under a virtual screen on a slow computer with 4 processor cores and no graphics card. If it stops answering, start it again with: xvfb-run -a ${BLENDER} --background --online-mode --command blender_mcp --host 127.0.0.1 --port 9876 (run in the background) and carry on; its scene is lost when it stops, so save your work often.
DELIVER: the scene saved as ${F}/village.blend; four pictures at 1200 x 800 saved as JPG files in ${F}/pictures/: a wide view of the whole village from above, a view standing on the road at eye height looking along it, a close view of the stable, a close view of one cottage; plus one close-up of the road surface. Then a plain-words report of what you built and how.
RULES, strictly: work only in the folder ${F}. Do not read, list or search any other file or folder on this computer (no other projects, plugins, notes, scratch folders, home folders, session or transcript files, git history, CLAUDE.md files). Do not use the Skill tool or any skill. Do not use the internet in any way: no downloads, no web search or fetch, no image generation, no reference pictures. Use no rented or remote machines. Do not commit or push anything.`, { model: 'sonnet', effort: 'max', label: 'build the village without the plugin (Sonnet, max)', phase: 'Build' })

return { report }