// What this does: runs one workflow file (workflows/build-a-place.js, written for the Workflow tool) on this computer WITHOUT any
// real helper: it gives the script its own args, agent(), parallel(), pipeline(), phase(), log() and budget, answers every agent()
// call with a canned object chosen by the call's label, and prints one JSON document on standard output saying what happened:
// the result (or the error), every agent call (label, phase, effort, the whole prompt, whether the canned answer fitted the schema),
// the phases in the order they began, the log lines, and how many calls of each kind ran at the same moment.
//
// Use (test_build_a_place_workflow.py does this):
//   node workflow_harness.mjs WORKFLOW.js SCENARIO.json FIXTURES_FOLDER
// SCENARIO.json: { "args": { ... the workflow's args ... },
//                  "responses": { "plan": "plan.json",               exact label -> a fixture file name
//                                 "build:*": "part-report.json",     a label before the colon, then * -> a fixture file name
//                                 "~^audit\\d*$": ["a.json", "b.json"],   a key that starts with ~ is a regular expression; a list is
//                                                                    used one answer at a time (the last one repeats)
//                                 "render": null,                    a helper that returns nothing (null)
//                                 "gate": { "inline": "object" } } } an object is the answer as it stands
// In a fixture file, {owner} is replaced by the text after the colon in the label (build:cottages gives cottages).
// A call with no canned answer stops the run with an error that names the label, so a script that asks for something new is noticed.
// The harness also refuses what the real tool refuses or what would break resume: Date.now, Math.random and new Date() with no
// argument throw, and the script runs in strict mode. It checks that every schema is well formed (every required name is a property)
// and that every canned answer fits the schema it was asked for; it only records a misfit, so the test can say so.
import fs from 'node:fs'
import path from 'node:path'

const [workflowPath, scenarioPath, fixturesFolder] = process.argv.slice(2)
if (!workflowPath || !scenarioPath || !fixturesFolder) {
  console.error('usage: node workflow_harness.mjs WORKFLOW.js SCENARIO.json FIXTURES_FOLDER')
  process.exit(2)
}
const source = fs.readFileSync(workflowPath, 'utf8')
const scenario = JSON.parse(fs.readFileSync(scenarioPath, 'utf8'))

// ---- the meta block: found by counting braces (it must be a pure literal), then read as a literal
function findMeta(text) {
  const start = text.indexOf('export const meta = {')
  if (start < 0) throw new Error('the script does not start with export const meta = {')
  let depth = 0
  let position = text.indexOf('{', start)
  let quote = null
  const begin = position
  for (; position < text.length; position++) {
    const character = text[position]
    if (quote) {
      if (character === '\\') position++
      else if (character === quote) quote = null
    } else if (character === '"' || character === "'" || character === '`') quote = character
    else if (character === '{') depth++
    else if (character === '}') { depth--; if (depth === 0) { position++; break } }
  }
  return { literal: text.slice(begin, position), end: position }
}
const metaInfo = findMeta(source)
const impure = /=>|\bfunction\b|`|\$\{|\.\.\.|\bnew\b|\(/.test(metaInfo.literal.replace(/"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/g, ''))
const meta = new Function(`return (${metaInfo.literal})`)()

// ---- schema helpers
function schemaShapeProblems(schema, where, problems) {
  if (!schema || typeof schema !== 'object') { problems.push(`${where}: no schema`); return }
  if (schema.type === 'object') {
    if (!schema.properties) problems.push(`${where}: an object schema without properties`)
    for (const name of schema.required ?? []) if (!(name in (schema.properties ?? {}))) problems.push(`${where}: required name ${name} is not a property`)
    for (const [name, sub] of Object.entries(schema.properties ?? {})) schemaShapeProblems(sub, `${where}.${name}`, problems)
  } else if (schema.type === 'array') {
    if (!schema.items) problems.push(`${where}: an array schema without items`)
    else schemaShapeProblems(schema.items, `${where}[]`, problems)
  }
}
function checkAnswerAgainstSchema(schema, value, where, problems) {
  if (!schema) return
  const kind = schema.type
  if (kind === 'object') {
    if (value === null || typeof value !== 'object' || Array.isArray(value)) { problems.push(`${where}: not an object`); return }
    for (const name of schema.required ?? []) if (!(name in value)) problems.push(`${where}.${name}: missing`)
    for (const [name, sub] of Object.entries(schema.properties ?? {})) if (name in value) checkAnswerAgainstSchema(sub, value[name], `${where}.${name}`, problems)
  } else if (kind === 'array') {
    if (!Array.isArray(value)) problems.push(`${where}: not a list`)
    else value.forEach((item, index) => checkAnswerAgainstSchema(schema.items, item, `${where}[${index}]`, problems))
  } else if (kind === 'string') {
    if (typeof value !== 'string') problems.push(`${where}: not text`)
    else if (schema.enum && !schema.enum.includes(value)) problems.push(`${where}: ${JSON.stringify(value)} is not one of ${schema.enum.join(', ')}`)
  } else if (kind === 'number') {
    if (typeof value !== 'number') problems.push(`${where}: not a number`)
  } else if (kind === 'boolean') {
    if (typeof value !== 'boolean') problems.push(`${where}: not true or false`)
  }
}

// ---- the canned answers
const counters = new Map()
function answerFor(label) {
  const responses = scenario.responses ?? {}
  const owner = label.includes(':') ? label.slice(label.indexOf(':') + 1) : ''
  let key = null
  if (label in responses) key = label
  else {
    const prefix = label.includes(':') ? `${label.slice(0, label.indexOf(':'))}:*` : null
    if (prefix && prefix in responses) key = prefix
    else key = Object.keys(responses).find((candidate) => candidate.startsWith('~') && new RegExp(candidate.slice(1)).test(label)) ?? null
  }
  if (key === null) throw new Error(`no canned answer for the helper labelled "${label}"`)
  let spec = responses[key]
  if (Array.isArray(spec)) {
    const used = counters.get(key) ?? 0
    counters.set(key, used + 1)
    spec = spec[Math.min(used, spec.length - 1)]
  }
  if (spec === null) return { key, value: null }
  if (typeof spec === 'string') {
    const text = fs.readFileSync(path.join(fixturesFolder, spec), 'utf8').replaceAll('{owner}', owner).replaceAll('{label}', label)
    return { key, value: JSON.parse(text) }
  }
  return { key, value: JSON.parse(JSON.stringify(spec)) }
}

// ---- the runtime the script is given
const calls = []
const logs = []
const phases = []
const inFlight = {}
const maxInFlight = {}
let currentPhase = null
const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds))

async function agent(prompt, options = {}) {
  const call = { index: calls.length, label: options.label ?? null, phase: options.phase ?? currentPhase, effort: options.effort ?? null, prompt, schema: options.schema ?? null,
    schema_problems: [], answer_key: null, answered: false }
  calls.push(call)
  if (typeof prompt !== 'string' || !prompt.trim()) call.schema_problems.push('the prompt is empty')
  if (options.schema) schemaShapeProblems(options.schema, call.label ?? 'schema', call.schema_problems)
  const group = (call.label ?? 'unlabelled').split(':')[0].replace(/\d+$/, '')
  inFlight[group] = (inFlight[group] ?? 0) + 1
  maxInFlight[group] = Math.max(maxInFlight[group] ?? 0, inFlight[group])
  try {
    await sleep(3)
    const { key, value } = answerFor(call.label ?? '')
    call.answer_key = key
    call.answered = value !== null
    if (value !== null && options.schema) checkAnswerAgainstSchema(options.schema, value, call.label, call.schema_problems)
    return value
  } finally {
    inFlight[group] -= 1
  }
}
async function parallel(thunks) {
  return Promise.all(thunks.map(async (thunk) => {
    try { return await thunk() } catch (problem) { logs.push(`(a parallel task threw: ${problem && problem.message})`); return null }
  }))
}
async function pipeline(items, ...stages) {
  return Promise.all(items.map(async (item, index) => {
    try {
      let value = item
      for (const stage of stages) value = await stage(value, item, index)
      return value
    } catch (problem) { return null }
  }))
}
const phase = (title) => { phases.push(title); currentPhase = title }
const log = (message) => { logs.push(String(message)) }
const budget = { total: null, spent: () => 0, remaining: () => Infinity }
const workflow = async () => { throw new Error('this workflow does not call other workflows') }

// ---- run the script: the body after the meta block, inside an async function, in strict mode
const body = `'use strict'\nconst meta = ${metaInfo.literal}\n${source.slice(metaInfo.end)}`
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const run = new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'budget', 'workflow', body)

const RealDate = Date
const realNow = Date.now
const realRandom = Math.random
function forbidClock() {
  Math.random = () => { throw new Error('Math.random is not allowed in a workflow (it would break resume)') }
  globalThis.Date = class extends RealDate {
    constructor(...given) {
      if (given.length === 0) throw new Error('new Date() with no argument is not allowed in a workflow (it would break resume)')
      super(...given)
    }
    static now() { throw new Error('Date.now is not allowed in a workflow (it would break resume)') }
  }
}
function allowClock() { Math.random = realRandom; globalThis.Date = RealDate; Date.now = realNow }

let result = null
let error = null
forbidClock()
try {
  result = await run(scenario.args, agent, parallel, pipeline, phase, log, budget, workflow)
} catch (problem) {
  error = problem && problem.message ? problem.message : String(problem)
} finally {
  allowClock()
}
process.stdout.write(JSON.stringify({ meta, meta_is_pure_literal: !impure, error, result: result === undefined ? null : result, calls, phases, logs, max_in_flight: maxInFlight }))
