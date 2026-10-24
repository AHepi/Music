export const meta = {
  name: 'verify-repo-assets',
  description: 'Check the repository alone can rebuild the films, its notes point at real files, and nothing important is missing',
  phases: [
    { title: 'Verify', detail: 'rebuild from a clean copy, check references, check completeness' },
  ],
}

const REPO = '/home/user/Music'
const KIT = '/home/user/work/paper-pop-up-film-kit'
const SCRATCH = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'

const REBUILD = {
  type: 'object',
  properties: {
    clone_ok: { type: 'boolean' },
    stills: { type: 'array', items: { type: 'object', properties: {
      scene: { type: 'string' }, time: { type: 'number' }, max_diff: { type: 'number' }, mean_diff: { type: 'number' }, verdict: { type: 'string' } },
      required: ['scene', 'time', 'verdict'] } },
    sound_check: { type: 'string' },
    problems: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['clone_ok', 'stills', 'problems', 'summary'],
}
const FINDINGS = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: { type: 'object', properties: {
      file: { type: 'string' }, problem: { type: 'string' }, suggested_fix: { type: 'string' }, severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } },
      required: ['file', 'problem', 'severity'] } },
    summary: { type: 'string' },
  },
  required: ['findings', 'summary'],
}

phase('Verify')
const [rebuild, refs, complete] = await parallel([
  () => agent(`You are checking that a git repository on its own can rebuild a narrated film's pictures and sound.
Work only in your own scratch folder ${SCRATCH}/rebuild-check (create it; delete nothing outside it). Do not commit, push or change anything in ${REPO} or ${KIT}.

Steps:
1. git clone ${REPO} ${SCRATCH}/rebuild-check/clone (a local clone of the committed state, branch ccr-e7298c9b-n19qkt).
2. The complete film kit is in the clone at austerity-explainer/film-kit/ (same layout as the working kit ${KIT}). Its paper-film/node_modules is not stored; copy it from ${KIT}/paper-film/node_modules (do not use the network).
3. Render stills from the CLONE's kit and from the WORKING kit at the same moments, and compare them pixel by pixel. From inside each kit folder run:
   node paper-film/tools/render-paper-film.mjs SCENE OUT_FOLDER --stills T1 T2 ...
   (read the top of render-paper-film.mjs first to confirm the exact arguments and scene names; list paper-film/scenes to find them).
   Scenes and moments: the chapter 1 scene (austerity-chapter-1) at 10 and 70 seconds; the chapter 2 scene (inflation-chapter-2) at 43.1, 100, 190 and 230 seconds (43.1 and 190 use the Blender models; 100 uses painted rooms).
   Compare each pair with Python (Pillow and numpy are available): report the largest and mean absolute difference per channel (0 to 255). Identical or a few levels of drawing noise is a pass; anything larger, or a missing picture, model or file error, is a problem. Note any errors the renderer prints (missing files, 404s).
   Rendering takes about 3 to 20 seconds a still; the machine has 4 processors, so run renders one at a time.
4. Sound: run, from the clone's film kit, python3 -I narration-tools/check_sound_alignment.py "${REPO}/austerity-explainer/chapter-2-inflation/deliver/20 Chapter 2 - what really causes inflation.mp4" <clone>/austerity-explainer/chapter-2-inflation/mix/chapter-2-mix.flac <clone>/austerity-explainer/chapter-2-inflation/narration/timeline.json and report its last line (it may need to read FLAC; if it fails on FLAC, say so exactly).
5. Also list any file the clone's kit code tries to load that is missing (look for 404s or file-not-found in render output).
Report what you ran and what came out, plainly.`, { label: 'rebuild from a clean copy', phase: 'Verify', schema: REBUILD, effort: 'medium' }),

  () => agent(`Check that the notes and guides in the git repository ${REPO} point at files that really exist, and that none of them now says something untrue about what is stored there.
Read-only: change nothing.
Files to check: ${REPO}/README.md; every .md directly in ${REPO}/austerity-explainer/ and in its project-notes/ and chapter-2-inflation/ folders; ${REPO}/austerity-explainer/film-kit/*.md (the kit's own start-here and how-to files) and film-kit/assets/soundtrack/00 What goes here.md.
For each file path or folder they mention (backticked paths, quoted file names such as "19 Chapter 2 - ...mp4", folder names), check whether it exists in the repository (use git ls-files and the working tree). Paths that clearly describe the working machine (for example /home/user/work/... or paper-film/out/... outputs) are fine if the text says so; flag them only if the text implies they are in the repository.
Especially check: README.md's "Traps" says the paintings, recordings and film kit are NOT stored in the repository. That is no longer true: the complete film kit (all paintings and paper pieces for both chapters, models, tools, examples, chapter 1 recordings) is now at austerity-explainer/film-kit/, except the soundtrack, which is deliberately left out because the repository is public. Also check project-notes/Status.md and the project story for claims like "not stored here" or "only in this session's working folder" that are now wrong or need the new location.
Report each problem with the file, the exact wording, and a suggested fix in plain words.`, { label: 'check references in notes', phase: 'Verify', schema: FINDINGS, effort: 'medium' }),

  () => agent(`Find any asset or script of this film project that is still missing from the git repository ${REPO}. Read-only: change nothing in the repository.
Working folders: ${KIT} (the film kit; ignore paper-film/node_modules and paper-film/out, which hold generated videos) and /home/user/work/chapter-2 (ignore stills/ = review screenshots, old-chunks/ = old video pieces, and the .mp4 masters, which are over GitHub's 100 MB file limit and can be filmed again).
Known and deliberate: the soundtrack "Tension and Gravity.mp3" is left out (the repository is public); chapter 2's working scripts, fix briefs, speed tests, round-20 working files and drafts were held back (they are in ${SCRATCH}/held-back) pending the owner's decision; Blender itself, its Python environments and the Blender MCP server's third-party source are not project files.
Method: run python3 -I ${SCRATCH}/content_inventory.py ${REPO} ${SCRATCH}/inventory-recheck.json ${KIT}/assets ${KIT}/paper-film/pieces ${KIT}/paper-film/scenes ${KIT}/paper-film/stage ${KIT}/paper-film/tools ${KIT}/paper-film/blender ${KIT}/examples ${KIT}/narration-tools /home/user/work/chapter-2/depth /home/user/work/chapter-2/paintings /home/user/work/chapter-2/masks /home/user/work/chapter-2/recordings /home/user/work/chapter-2/transcripts /home/user/work/chapter-2/reference
(it lists files whose CONTENTS are not anywhere in the repository; renamed copies count as present). Also compare /home/user/work/chapter-2's top-level files (word-times.json, timeline.json, mix.mp3, mix.wav, narration.wav) against the repository's austerity-explainer/chapter-2-inflation/narration and mix folders (mix.wav and narration.wav were stored as lossless .flac; that counts as present).
Also check the plugin copy ${REPO}/plugins/explainer-film/kit against ${KIT}: list code files (scenes, stage, tools, blender, narration-tools) whose plugin copy differs from the working kit, since the plugin should carry the latest tools.
For each missing or out-of-date item say what it is, whether it matters (an asset or script needed to rebuild or understand the films) and where it should go.`, { label: 'check nothing is missing', phase: 'Verify', schema: FINDINGS, effort: 'medium' }),
])

return { rebuild, refs, complete }
