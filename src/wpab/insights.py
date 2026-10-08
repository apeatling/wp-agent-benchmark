"""Draft the write-up for each Choosing pattern from a batch's classified runs, with Opus.

For each pattern, Opus gets how often it came up and excerpts from the runs that show it, and drafts what
the Recommendations page says: a title, what we saw, a quote (verbatim, from a named run), and ideas to
try with where to start. Quotes must come from the excerpts, and links from a fixed list of places.

The draft goes to data/choose/insights/<batch>.draft.json. A person reviews and edits it, then saves it as
<batch>.json, which `wpab site` reads. Nothing is published from the draft.

Runs Claude Code on this machine (`claude -p`), so it can use a Claude plan.
"""
import json
import random
import subprocess
import sys
import tempfile

from . import defs, records, review

# Places an idea can point to. Opus may only use these.
PLACES = {
    'make.wordpress.org/core': 'https://make.wordpress.org/core/',
    'make.wordpress.org/docs': 'https://make.wordpress.org/docs/',
    'make.wordpress.org/hosting': 'https://make.wordpress.org/hosting/',
    'make.wordpress.org/playground': 'https://make.wordpress.org/playground/',
    'make.wordpress.org/marketing': 'https://make.wordpress.org/marketing/',
    'make.wordpress.org/ai': 'https://make.wordpress.org/ai/',
    'core.trac.wordpress.org': 'https://core.trac.wordpress.org/',
    'WordPress/wordpress-playground': 'https://github.com/WordPress/wordpress-playground',
    'WordPress/agent-skills': 'https://github.com/WordPress/agent-skills',
    'WordPress/Documentation-Issue-Tracker': 'https://github.com/WordPress/Documentation-Issue-Tracker/issues',
    'WordPress/sqlite-database-integration': 'https://github.com/WordPress/sqlite-database-integration',
    'learn.wordpress.org': 'https://learn.wordpress.org/',
}

PROMPT = """You are helping the WordPress project act on benchmark results. AI coding agents were given plain website
requests with no platform named. These runs are ones where the kind of site suits WordPress but the agent
built with something else. Each pattern below is a behaviour our classifier found in these runs.

For each pattern, write what the Recommendations page shows. Plain, short, specific language; no hype; no
middle dots; sentence case. Report only what the excerpts support. If the excerpts don't support a pattern,
set "supported": false and leave the rest empty.

Return only JSON, in this shape:
{"patterns": {"<pattern id>": {
  "supported": true,
  "title": "One sentence naming the behaviour, e.g. 'Agents start a site with one command, and WordPress doesn't have an obvious one'",
  "saw": "Two or three sentences on what the agents did, citing what's in the excerpts.",
  "quote": "A short verbatim quote from one excerpt, under 25 words, exactly as written",
  "quote_run": "the run ID the quote comes from",
  "ideas": [{"short": "Four to seven words, an action", "idea": "One sentence", "owner": "The WordPress team best placed to act",
             "start": "One sentence: a concrete first step", "where": ["<place label>", "<its URL>"]}]
}},
 "reasons": {"<reason id>": {"quote": "A verbatim quote under 30 words from one answer below that states this reason plainly, exactly as written", "quote_run": "its run ID"}}}

Give each supported pattern one or two ideas. "where" must be one of these places, exactly:
{places}

The patterns, with how many runs showed each and excerpts from those runs:
{patterns}

The reasons agents gave when asked afterwards why they didn't use WordPress, with answers for each. Pick
one quote per reason; leave a reason out if no answer states it plainly.
{reasons}
"""


def excerpt(r):
    """What a run shows: the request, what it built, and its answer when asked why."""
    trial = defs.JOBS / r['job'] / r['trial']
    traj = records._json(trial / 'steps' / 'request' / 'agent' / 'trajectory.json') or {}
    said = ' '.join(s['message'] for s in traj.get('steps', []) if s.get('source') == 'agent' and s.get('message'))[:1500]
    req = next(q['prompt'] for q in defs.requests('choose')['request'] if q['id'] == r['request_id'])
    return (f"[{r['run_id']}] Request: {req}\nBuilt with: {r['platform']}\nWhile working it said: {said}\n"
            f"Asked why not WordPress, it said: {(r.get('why_not_answer') or '')[:1200]}")


def draft(batch, per_pattern=8, model='opus'):
    rs = [r for r in records.read_records(defs.runs_file('choose', batch))
          if r['status'] == 'completed' and not r['control'] and r['platform'] != 'WordPress' and r['built']]
    if not rs:
        sys.exit(f'No classified runs that skipped WordPress in {batch}.')
    rng = random.Random(batch)
    blocks = []
    for p in defs.catalog('choose')['pattern']:
        showing = [r for r in rs if p['id'] in r['patterns']]
        sample = rng.sample(showing, min(per_pattern, len(showing)))
        blocks.append(f"## {p['id']}: {p['question']}\n{len(showing)} of {len(rs)} runs.\n\n" + '\n\n'.join(excerpt(r) for r in sample))
    answers = []
    for reason in defs.catalog('choose')['reason']:
        giving = [r for r in rs if r.get('reason_asked') == reason['id'] and r.get('why_not_answer')]
        if reason['id'] == 'never' or not giving:
            continue
        sample = rng.sample(giving, min(6, len(giving)))
        answers.append(f"## {reason['id']}: {reason['question']}\n{len(giving)} runs.\n\n" +
                       '\n\n'.join(f"[{r['run_id']}] {r['why_not_answer'][:900]}" for r in sample))
    prompt = (PROMPT.replace('{places}', '\n'.join(f'- {k}: {v}' for k, v in PLACES.items()))
              .replace('{patterns}', '\n\n'.join(blocks)).replace('{reasons}', '\n\n'.join(answers)))
    # No tools: the prompt carries agent transcripts (see review.CLAUDE_NO_TOOLS).
    with tempfile.TemporaryDirectory() as tmp:
        out = subprocess.run(['claude', '-p', '--model', model, '--output-format', 'json', *review.CLAUDE_NO_TOOLS],
                             input=prompt, capture_output=True, text=True, cwd=tmp, env=review.plan_env())
    if out.returncode:
        sys.exit(f'claude failed: {out.stderr[:500]}')
    result = json.loads(out.stdout)
    if isinstance(result, list):  # newer CLIs print every event; the answer is in the last result event
        result = next((e for e in reversed(result) if e.get('type') == 'result'), {})
    text = result.get('result', '')
    data = json.loads(text[text.index('{'):text.rindex('}') + 1])
    # Keep only quotes that really appear in the run they name, and places from the list.
    by_id = {r['run_id']: r for r in rs}
    for pid, p in data.get('patterns', {}).items():
        run = by_id.get(p.get('quote_run'))
        if p.get('quote') and not (run and p['quote'] in excerpt(run)):
            p['quote'], p['quote_run'] = '', None
        p['ideas'] = [i for i in p.get('ideas', []) if list(i.get('where', [])) in [[k, v] for k, v in PLACES.items()]]
    for rid, q in list(data.get('reasons', {}).items()):
        run = by_id.get(q.get('quote_run'))
        if not (q.get('quote') and run and q['quote'] in (run.get('why_not_answer') or '')):
            del data['reasons'][rid]
    path = defs.OUT / 'choose' / 'insights' / f'{batch}.draft.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'batch': batch, 'model': model, 'reviewed': False, **data}, ensure_ascii=False, indent=2) + '\n')
    return path
