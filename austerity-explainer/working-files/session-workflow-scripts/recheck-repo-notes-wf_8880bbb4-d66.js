export const meta = {
  name: 'recheck-repo-notes',
  description: 'Fresh check that the fixed notes point at real files and say nothing untrue about what is stored',
  phases: [{ title: 'Recheck' }],
}
const REPO = '/home/user/Music'
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
phase('Recheck')
const result = await agent(`Check that the notes and guides in the git repository ${REPO} (branch ccr-e7298c9b-n19qkt, latest commit) point at files that really exist, and say nothing untrue about what the repository holds. Read-only: change nothing.
Facts: the complete film kit is at austerity-explainer/film-kit/ (paintings, pieces, models, tools, examples for chapters 1 and 2); the soundtrack "Tension and Gravity.mp3" is deliberately not stored (public repository); full-quality film files are not stored (too big); chapter 2's working files from the session are held back pending the owner's decision. Paths described as an earlier or working machine's (for example /home/user/work/..., chapter 1's original working folder) are fine when the text says so.
Files: ${REPO}/README.md; every .md directly in ${REPO}/austerity-explainer/, its project-notes/ and chapter-2-inflation/; ${REPO}/austerity-explainer/film-kit/*.md, film-kit/assets/soundtrack/00 What goes here.md, film-kit/paper-film/pieces/00 What goes here.md; ${REPO}/plugins/explainer-film/README.md.
For each backticked path or quoted file name, check it exists (git ls-files plus the working tree), unless the text marks it as elsewhere. Also check the facts above are stated consistently (no file still says the kit is only in zip files, that the soundtrack is in the repository, or that a master film is stored).
Report only real problems, each with file, exact wording and a fix. An empty list is a fine answer.`, { label: 'recheck notes', phase: 'Recheck', schema: FINDINGS, effort: 'medium' })
return result
