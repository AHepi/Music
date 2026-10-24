# What this does: waits until the village run's ground step has reported back (its result is in the run's journal), then exits,
# so the main session can switch the later helpers to high effort at that moment.
import json, time
JOURNAL = '/root/.claude/projects/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/subagents/workflows/wf_2b344eca-8d9/journal.jsonl'
while True:
    events = [json.loads(line) for line in open(JOURNAL) if line.strip()]
    results = sum(1 for event in events if event.get('type') == 'result')
    if results >= 2:
        print(time.strftime('%H:%M:%S'), 'the ground step has reported back;', len(events), 'journal lines')
        break
    time.sleep(20)
