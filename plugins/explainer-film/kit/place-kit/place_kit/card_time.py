"""What this does: the CARD-TIME LEDGER and the ALLOWANCE. Every job sent to a rented card is written into one ledger file (a text file, one line for each job) with its
billed seconds, and each helper has an allowance of card minutes (house numbers place_card_time.*: a builder 10, a fixer 5, a renderer 10, a checker 3, a planner 0 ...).
Before a paid step starts, check() says whether it fits: it says OK, warns when 80 percent is used, and REFUSES when the step would pass the allowance. To go over, a helper must write
a reason of at least 15 letters (--over-allowance "reason"), the reason is written into the ledger, and even then nothing may pass the allowance by more than half again: past that the
person decides. The whole job has a total too (`card-time start --team-minutes N` writes the person's own cap; without it the house number is used).
Plain Python (standard library only); no Blender needed. It never reads or prints a key or an endpoint id.

How seconds are counted (cautiously, so a number is never too small): card seconds = work seconds + wake-up seconds + the idle tail (place_card_time.idle_tail_seconds, a worker stays
up about 5 seconds after its last job). A price shown from seconds ("about US$0.07") is an estimate from the hourly price of the day, never a bill: one bill once came out above the
estimate and was never explained.

A concrete example: a builder has used 480 s of its 600 s. check(entries, 'builder-ground', 'builder', estimate_seconds=200) answers 'refuse': 480 + about 200 is 680 s, over 600 s.
With over_reason="the first batch missed the wall, one more batch is needed" it answers 'warn' (680 s is inside 600 x 1.5 = 900 s) and the reason goes into the ledger.

Where the ledger is: --ledger FILE, else the environment variable PLACE_CARD_LEDGER, else card-time-ledger.jsonl in the folder you run in. Every rented-card command prints the ledger it used.
Who is who: --helper NAME (else PLACE_HELPER, else "unnamed-helper") and --role builder|fixer|integrator|renderer|checker|planner (else PLACE_HELPER_ROLE, else "default").
The verb: `explainer-film-place card-time show | check | add | start`. Exit: 0 fine, 1 refused, 2 an input is unusable.
"""
import json
import os
import threading
import time

from . import house_numbers as numbers

LEDGER_NAME = 'card-time-ledger.jsonl'
ENV_LEDGER, ENV_HELPER, ENV_ROLE = 'PLACE_CARD_LEDGER', 'PLACE_HELPER', 'PLACE_HELPER_ROLE'
ROLES = ('builder', 'fixer', 'integrator', 'renderer', 'checker', 'planner', 'default')
_write_lock = threading.Lock()


class LedgerProblem(Exception):
    """The ledger or an input to it cannot be used (exit 2)."""


# ------------------------------------------------------------------ who and where
def ledger_path(explicit=None, environ=None):
    environ = os.environ if environ is None else environ
    chosen = explicit or environ.get(ENV_LEDGER) or os.path.join(os.getcwd(), LEDGER_NAME)
    return os.path.abspath(chosen)


def who(parsed=None, environ=None):
    """(helper, role) from the options, else the environment, else the plain defaults."""
    environ = os.environ if environ is None else environ
    helper = (getattr(parsed, 'helper', None) or environ.get(ENV_HELPER) or 'unnamed-helper').strip()
    role = (getattr(parsed, 'role', None) or environ.get(ENV_ROLE) or 'default').strip().lower()
    return helper, role


def now_text():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


# ------------------------------------------------------------------ reading and writing
def read_ledger(path):
    """(entries, problems): the entries in file order; a line that is not JSON is reported and skipped (never silently)."""
    if not os.path.exists(path):
        return [], []
    entries, problems = [], []
    with open(path, encoding='utf-8') as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                problems.append(f'line {number} of the ledger is not JSON and was skipped')
                continue
            if isinstance(entry, dict):
                entries.append(entry)
            else:
                problems.append(f'line {number} of the ledger is not an entry and was skipped')
    return entries, problems


def append_entry(path, entry):
    entry = dict(entry)
    entry.setdefault('when', now_text())
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with _write_lock:
        with open(path, 'a', encoding='utf-8') as handle:
            handle.write(json.dumps(entry, sort_keys=True) + '\n')
    return entry


# ------------------------------------------------------------------ the numbers
def idle_tail_seconds():
    return float(numbers.value('place_card_time.idle_tail_seconds'))


def allowance_minutes(role):
    key = f'place_card_time.allowance_minutes.{role}'
    return float(numbers.value(key if numbers.has(key) else 'place_card_time.allowance_minutes.default'))


def allowance_seconds(role):
    return allowance_minutes(role) * 60.0


def card_seconds_of(work_ms=0, wake_up_ms=0, tail=True):
    """The pieces of one job's card seconds and their sum (work + wake-up + the idle tail)."""
    work = round(float(work_ms or 0) / 1000.0, 1)
    wake = round(float(wake_up_ms or 0) / 1000.0, 1)
    tail_seconds = idle_tail_seconds() if tail else 0.0
    return {'work_seconds': work, 'wake_up_seconds': wake, 'idle_tail_seconds': tail_seconds, 'card_seconds': round(work + wake + tail_seconds, 1)}


def dollars_text(seconds):
    price = float(numbers.value('place_render.card_dollars_per_hour'))
    return f'about US${seconds * price / 3600.0:.2f} (an estimate at the price of the day, US${price} an hour; not a bill)'


def used_seconds(entries, helper):
    return round(sum(float(e.get('card_seconds') or 0) for e in entries if e.get('helper') == helper and e.get('kind') in ('job', 'small', 'manual')), 1)


def team_used_seconds(entries):
    return round(sum(float(e.get('card_seconds') or 0) for e in entries if e.get('kind') in ('job', 'small', 'manual')), 1)


def team_total_seconds(entries):
    """The person's cap from the newest `start` entry, else the house number."""
    for entry in reversed(entries):
        if entry.get('kind') == 'start' and entry.get('team_minutes'):
            return float(entry['team_minutes']) * 60.0
    return float(numbers.value('place_card_time.team_total_minutes')) * 60.0


def batch_count(entries, helper, change):
    return sum(1 for e in entries if e.get('kind') == 'batch' and e.get('helper') == helper and e.get('change') == change)


def logged_job_ids(entries):
    return {e.get('job_id') for e in entries if e.get('job_id')}


# ------------------------------------------------------------------ the check
def check(entries, helper, role, estimate_seconds=0.0, over_reason=None, what='this paid step'):
    """Whether a paid step of about estimate_seconds fits. Returns {'status': 'ok'|'warn'|'refuse', 'lines': [...], 'used', 'allowance', 'projected', 'override': bool, 'team_used', 'team_total'}."""
    allowance = allowance_seconds(role)
    used = used_seconds(entries, helper)
    projected = round(used + float(estimate_seconds or 0.0), 1)
    team_used, team_total = team_used_seconds(entries), team_total_seconds(entries)
    extra = float(numbers.value('place_card_time.override_extra_share'))
    warn_share = float(numbers.value('place_card_time.warn_share'))
    letters = int(numbers.value('place_card_time.override_reason_letters_min'))
    reason = (over_reason or '').strip()
    result = {'status': 'ok', 'lines': [], 'used': used, 'allowance': allowance, 'projected': projected, 'override': False, 'team_used': team_used, 'team_total': team_total, 'role': role, 'helper': helper}
    words = f'{helper} (role {role}) has used {used:.0f} s of {allowance:.0f} s ({allowance / 60:g} min)'
    if estimate_seconds:
        words += f'; {what} needs about {float(estimate_seconds):.0f} s more, {projected:.0f} s in all'
    if team_total and team_used + float(estimate_seconds or 0.0) > team_total:
        result['status'] = 'refuse'
        result['lines'].append(f'FAIL card time: the whole job has used {team_used:.0f} s of its {team_total:.0f} s ({team_total / 60:g} min) and {what} would pass it. Stop and tell the person: only they raise the total '
                               '(card-time start --team-minutes N).')
        return result
    if allowance <= 0:
        result['status'] = 'refuse'
        result['lines'].append(f'FAIL card time: the role {role} has no card time ({words}). Ask the integrator for the picture you need.')
        return result
    if projected < allowance * warn_share:
        result['lines'].append(f'PASS card time: {words}.')
        return result
    if projected <= allowance:
        result['status'] = 'warn'
        result['lines'].append(f'LOOK card time: {words}: that is {warn_share:.0%} or more of the allowance. Plan the rest with fewer pictures.')
        return result
    # over the allowance
    if len(reason) >= letters and projected <= allowance * (1.0 + extra):
        result['status'] = 'warn'
        result['override'] = True
        result['lines'].append(f'LOOK card time: OVER THE ALLOWANCE by {projected - allowance:.0f} s ({words}). Allowed only because of the reason you wrote: "{reason}". It is written into the ledger.')
        return result
    if len(reason) >= letters:
        result['status'] = 'refuse'
        result['lines'].append(f'FAIL card time: {words}. Even with a reason nothing may pass the allowance by more than {extra:.0%} ({allowance * (1.0 + extra):.0f} s). Stop and tell the person.')
        return result
    result['status'] = 'refuse'
    result['lines'].append(f'FAIL card time: {words}. That is over the allowance, so nothing was sent. Make fewer variations, draw smaller, or finish what you have. To go over by up to {extra:.0%} '
                           f'add --over-allowance "a reason of at least {letters} letters"; the reason is written into the ledger and the person reads it.')
    return result


def check_batch(entries, helper, change, over_reason=None):
    """The batch rule: one batch for a change, look at the sheet, at most one more (place_card_time.batches_per_change_max). Returns {'status', 'number', 'lines'}."""
    maximum = int(numbers.value('place_card_time.batches_per_change_max'))
    done = batch_count(entries, helper, change)
    number = done + 1
    letters = int(numbers.value('place_card_time.override_reason_letters_min'))
    if number > maximum:
        if len((over_reason or '').strip()) >= letters:
            return {'status': 'warn', 'number': number, 'override': True, 'lines': [f'LOOK batches: batch {number} for the change "{change}" is over the rule of {maximum}; allowed only because of the reason you wrote: "{over_reason.strip()}".']}
        return {'status': 'refuse', 'number': number, 'lines': [f'FAIL batches: {helper} already drew {done} batch(es) for the change "{change}" (the rule: one batch, look, at most one more). Pick or combine the best '
                                                                f'versions and go on; to draw another add --over-allowance "a reason of at least {letters} letters".']}
    if number == maximum:
        return {'status': 'warn', 'number': number, 'lines': [f'LOOK batches: this is batch {number} of {maximum} for the change "{change}": the last one. After it, pick or combine and go on.']}
    return {'status': 'ok', 'number': number, 'lines': [f'PASS batches: batch {number} of at most {maximum} for the change "{change}".']}


# ------------------------------------------------------------------ writing what happened
def log_job(path, helper, role, summary, what, where='card', extra=None):
    """Writes one rented-card job (its job summary: id, wake_up_ms, billed_work_ms) into the ledger, unless that job id is already there. Returns the entry or None."""
    job_id = summary.get('id')
    entries, _ = read_ledger(path)
    if job_id and job_id in logged_job_ids(entries):
        return None
    pieces = card_seconds_of(summary.get('billed_work_ms'), summary.get('wake_up_ms'))
    entry = {'kind': 'job', 'helper': helper, 'role': role, 'what': what, 'job_id': job_id, 'where': where, 'status': summary.get('runpod_status'), 'measured': True, **pieces}
    if extra:
        entry.update(extra)
    return append_entry(path, entry)


def log_small_jobs(path, helper, role, small_jobs, what):
    """Writes the small jobs of one command (uploads, checks, downloads) as one entry. Returns the entry or None when there were none."""
    if not small_jobs:
        return None
    work_ms = sum(float(job.get('work_ms') or 0) for job in small_jobs)
    wake_ms = sum(float(job.get('wake_up_ms') or 0) for job in small_jobs)
    pieces = card_seconds_of(work_ms, wake_ms)
    return append_entry(path, {'kind': 'small', 'helper': helper, 'role': role, 'what': f'{what} ({len(small_jobs)} small job(s): uploads, checks, downloads)', 'jobs': len(small_jobs), 'measured': True, **pieces})


def log_wall_clock(path, helper, role, seconds, what):
    """For a client that cannot say what a step billed (the older command-line client): the seconds the step took on the wall clock, which is at least as long as the worker was up. Marked as an estimate."""
    pieces = {'work_seconds': round(float(seconds), 1), 'wake_up_seconds': 0.0, 'idle_tail_seconds': idle_tail_seconds()}
    pieces['card_seconds'] = round(pieces['work_seconds'] + pieces['idle_tail_seconds'], 1)
    return append_entry(path, {'kind': 'small', 'helper': helper, 'role': role, 'what': what, 'measured': False, 'estimate_note': 'counted from the wall clock because this client does not say what the step billed', **pieces})


def log_override(path, helper, role, reason, what):
    return append_entry(path, {'kind': 'override', 'helper': helper, 'role': role, 'what': what, 'reason': reason})


def log_batch(path, helper, role, change, number, variations, jobs):
    return append_entry(path, {'kind': 'batch', 'helper': helper, 'role': role, 'change': change, 'number': number, 'variations': variations, 'jobs': jobs})


# ------------------------------------------------------------------ what a helper sees
def show_lines(path, entries, helper=None, role=None):
    lines = [f'Card-time ledger: {path}']
    team_total = team_total_seconds(entries)
    team_used = team_used_seconds(entries)
    lines.append(f'The whole job: {team_used:.0f} s used of {team_total:.0f} s ({team_total / 60:g} min); {dollars_text(team_used)}.')
    helpers = sorted({e.get('helper') for e in entries if e.get('helper')} | ({helper} if helper else set()))
    for name in helpers:
        own = [e for e in entries if e.get('helper') == name]
        role_of = next((e.get('role') for e in reversed(own) if e.get('role')), 'default')
        if name == helper and role:
            role_of = role
        allowance = allowance_seconds(role_of)
        used = used_seconds(entries, name)
        share = (used / allowance) if allowance else (1.0 if used else 0.0)
        lines.append(f'  {name} (role {role_of}): used {used:.0f} s of {allowance:.0f} s ({share:.0%}); left {max(0.0, allowance - used):.0f} s')
        for entry in own:
            if entry.get('kind') in ('job', 'small', 'manual'):
                flag = '' if entry.get('measured', True) else ' (estimate from the wall clock)'
                lines.append(f'      {entry.get("when", "")} {entry.get("kind")}: work {entry.get("work_seconds", 0)} + wake-up {entry.get("wake_up_seconds", 0)} + idle {entry.get("idle_tail_seconds", 0)} = '
                             f'{entry.get("card_seconds", 0)} s{flag}  {entry.get("what", "")}')
            elif entry.get('kind') == 'override':
                lines.append(f'      {entry.get("when", "")} OVER-ALLOWANCE reason: {entry.get("reason", "")} ({entry.get("what", "")})')
            elif entry.get('kind') == 'batch':
                lines.append(f'      {entry.get("when", "")} batch {entry.get("number")} for "{entry.get("change")}": {entry.get("variations")} variation(s) in {entry.get("jobs")} job(s)')
    return lines


# ------------------------------------------------------------------ the verb
def main_command(parsed, environ=None, say=print):
    """`card-time show | check | add | start`. Returns the exit code."""
    try:
        path = ledger_path(getattr(parsed, 'ledger', None), environ)
        helper, role = who(parsed, environ)
        action = getattr(parsed, 'action', None) or 'show'
        entries, problems = read_ledger(path)
        for problem in problems:
            say(f'LOOK ledger: {problem}')
        if role not in ROLES:
            raise LedgerProblem(f'the role "{role}" is not one of {", ".join(ROLES)}')
        if action == 'show':
            for line in show_lines(path, entries, helper if getattr(parsed, 'helper', None) else None, role if getattr(parsed, 'role', None) else None):
                say(line)
            return 0
        if action == 'check':
            result = check(entries, helper, role, estimate_seconds=getattr(parsed, 'estimate_seconds', None) or 0.0, over_reason=getattr(parsed, 'over_allowance', None))
            for line in result['lines']:
                say(line)
            say(f'ledger: {path}')
            return 1 if result['status'] == 'refuse' else 0
        if action == 'add':
            work, wake = getattr(parsed, 'work_seconds', None), getattr(parsed, 'wake_up_seconds', None)
            if work is None:
                raise LedgerProblem('card-time add needs --work-seconds N (the billed work seconds of a job you ran by hand; --wake-up-seconds M too when the summary says it)')
            what = getattr(parsed, 'what', None) or 'a job logged by hand'
            job_id = getattr(parsed, 'job_id', None)
            if job_id and job_id in logged_job_ids(entries):
                say(f'LOOK ledger: job {job_id} is already in the ledger; nothing was added')
                return 0
            pieces = card_seconds_of(float(work) * 1000.0, float(wake or 0.0) * 1000.0)
            entry = append_entry(path, {'kind': 'manual', 'helper': helper, 'role': role, 'what': what, 'job_id': job_id, 'measured': True, **pieces})
            say(f'PASS ledger: logged {entry["card_seconds"]} card seconds for {helper} in {path}')
            return 0
        if action == 'start':
            minutes = getattr(parsed, 'team_minutes', None)
            if not minutes or minutes <= 0:
                raise LedgerProblem('card-time start needs --team-minutes N (the most card minutes the whole job may use)')
            append_entry(path, {'kind': 'start', 'team_minutes': float(minutes), 'what': getattr(parsed, 'what', None) or 'the person\'s cap for this job', 'helper': helper})
            say(f'PASS ledger: the whole job may use {minutes:g} card minutes ({dollars_text(float(minutes) * 60)}) in {path}')
            return 0
        raise LedgerProblem(f'unknown card-time action: {action}')
    except LedgerProblem as problem:
        say(f'FAIL {problem}')
        return 2


def before_paid_step(parsed, estimate_seconds=0.0, what='this paid step', environ=None, say=print):
    """The gate every rented-card command passes first. Returns (ok, ledger path, helper, role). When it is not ok, the FAIL line was already said and nothing may be sent."""
    path = ledger_path(getattr(parsed, 'ledger', None), environ)
    helper, role = who(parsed, environ)
    entries, _ = read_ledger(path)
    result = check(entries, helper, role, estimate_seconds, getattr(parsed, 'over_allowance', None), what)
    for line in result['lines']:
        say(line)
    if result['status'] == 'refuse':
        return False, path, helper, role
    if result['override']:
        log_override(path, helper, role, (getattr(parsed, 'over_allowance', None) or '').strip(), what)
    return True, path, helper, role
