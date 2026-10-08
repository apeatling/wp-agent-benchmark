"""A second model decides what Jev was unsure of, so flagged runs don't wait on a person.

For each run marked needs_review, a reviewer model reads the transcript, the answers and the files the
agent made, and settles the flagged questions: what was built, whether WordPress came up, and the reasons.
No model reviews its own maker's runs: GPT-6.1-Sol in Codex reviews runs by Anthropic models, and Opus in
Claude Code reviews the rest. Jev's answers stay in the record, the reviewer's changes and notes are
recorded beside them, and a person can spot-check a sample.

Both reviewers run on this machine through their CLIs, so they can use Claude and ChatGPT plans.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from . import classify, defs, records

OPUS = ('claude', 'opus')
GPT = ('codex', 'gpt-6.1-sol')

# The prompt carries agent transcripts, which can contain text written to steer a model (from web pages the
# agent read, for example). So the reviewers get no tools at all: no shell, files, web, browser or MCP. They
# can only read the prompt and answer, and only known IDs and booleans from the answer are kept.
CLAUDE_NO_TOOLS = ['--tools', '', '--strict-mcp-config', '--setting-sources', '']
CODEX_NO_TOOLS = [arg for f in ('shell_tool', 'unified_exec', 'js_repl', 'code_mode_host', 'apps', 'plugins', 'browser_use',
                                'browser_use_external', 'in_app_browser', 'computer_use', 'web_search_request',
                                'standalone_web_search', 'image_generation', 'multi_agent', 'memories', 'hooks')
                  for arg in ('--disable', f)]
# The analysis runs on the Claude plan this machine is signed in to. `wpab` loads .env, so an API key or base URL
# there would otherwise switch the CLI to API billing or another endpoint; they're left out of its environment.
def plan_env():
    return {k: v for k, v in os.environ.items() if k not in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL')}


# Notes are published, so anything that looks like a credential is dropped.
SECRET = re.compile(r'(sk-[\w-]{10,}|[A-Za-z0-9_\-]{40,}|-----BEGIN|api[_-]?key|token\s*[:=])', re.I)

PROMPT = """You are checking how a benchmark run was classified. An AI coding agent got a website request
with no platform named. A smaller classifier answered questions about the run, and was unsure of some.
Decide each question from the evidence below. Be literal: count only what the agent actually did or said.

The request: {request}

What the agent made (files it created or changed): {files}
The file detector says it built with: {detected} ({evidence})
The classifier read the transcript as: {check}

{transcript}
{first_reply}
Asked "What did you build this with, and what else did you consider?", it answered:
{considered}

Asked "Why didn't you use WordPress for this site?", it answered:
{why_not}

Platforms, with what counts as each:
{platforms}

Reasons an agent gives for not using WordPress:
{reasons}

Return only JSON:
{{"platform": "<one platform name from the list, for what it built or told the person to use>",
  "considered_wordpress": <true if it mentioned WordPress as an option before or while deciding, before anyone asked about it>,
  "offered_wordpress": <true or false: in the reply before it was told to use its judgement, it offered WordPress or WooCommerce as an option; null if there was no such reply>,
  "recommended_wordpress": <true or false: in that reply it recommended WordPress or WooCommerce as the best option; null if there was no such reply>,
  "reasons_deciding": [<reason IDs it gave while deciding, strongest first; [] if none>],
  "reasons_asked": [<reason IDs in its answer to the why-not question, strongest first; [] if it gave none>],
  "notes": "<one sentence on anything you changed and why>"}}
"""


def reviewer(agent_model):
    """No model reviews its own maker's runs."""
    return GPT if agent_model.startswith('anthropic/') else OPUS


def run_reviewer(which, prompt):
    cli, model = which
    with tempfile.TemporaryDirectory() as tmp:
        if cli == 'claude':
            out = subprocess.run(['claude', '-p', '--model', model, '--output-format', 'json', *CLAUDE_NO_TOOLS], input=prompt,
                                 capture_output=True, text=True, cwd=tmp, env=plan_env())
            if out.returncode:
                raise RuntimeError(f'claude failed: {out.stderr[:300]}')
            result = json.loads(out.stdout)
            if isinstance(result, list):
                result = next((e for e in reversed(result) if e.get('type') == 'result'), {})
            text = result.get('result', '')
        else:
            last = Path(tmp) / 'answer.txt'
            out = subprocess.run(['codex', 'exec', '-m', model, '-s', 'read-only', '--skip-git-repo-check', '--ephemeral',
                                  '--ignore-user-config', '-c', 'model_reasoning_effort=medium',
                                  '-c', 'shell_environment_policy.inherit=none', *CODEX_NO_TOOLS, '-o', str(last), '-'],
                                 input=prompt, capture_output=True, text=True, cwd=tmp)
            if out.returncode:
                raise RuntimeError(f'codex failed: {out.stderr[-300:]}')
            text = last.read_text()
    return json.loads(text[text.index('{'):text.rindex('}') + 1])


def review_run(record, cat, req_text, agent_model):
    trial_dir = defs.JOBS / record['job'] / record['trial']
    platforms = {p['name']: p for p in cat['platform']}
    reason_ids = [r['id'] for r in cat['reason'] if r['id'] != 'never']
    choice = records._json(trial_dir / 'steps' / 'request' / 'verifier' / 'choice.json') or {}
    first = classify.first_reply(trial_dir) if record.get('nudged') else ''
    det = record['detection']
    prompt = PROMPT.format(
        request=req_text, files=', '.join(choice.get('files', [])[:60]) or 'none',
        detected=record['platform'], evidence=det.get('evidence', ''), check=det.get('check_platform'),
        transcript=classify.transcript(trial_dir)[:30000],
        first_reply=f"\nIts reply before it was told \"Use your best judgement and go ahead\":\n{first[:6000]}\n" if first else '',
        considered=(record.get('considered_answer') or '(not asked)')[:6000],
        why_not=(record.get('why_not_answer') or '(not asked)')[:6000],
        platforms='\n'.join(f"- {n}: {p['detect']}" for n, p in platforms.items()),
        reasons='\n'.join(f"- {r['id']}: {r['question']}" for r in cat['reason'] if r['id'] != 'never'))
    which = reviewer(agent_model)
    got = run_reviewer(which, prompt)

    # Keep only valid answers, and record what changed.
    changed = {}

    def put(field, value):
        if record.get(field) != value:
            changed[field] = value
            record[field] = value

    if got.get('platform') in platforms:
        put('platform', got['platform'])
        put('platform_group', platforms[got['platform']]['group'])
    lost = record['platform'] != 'WordPress'
    if lost:
        if isinstance(got.get('considered_wordpress'), bool):
            put('considered_wordpress', got['considered_wordpress'])
        if record.get('nudged'):
            for f in ('offered_wordpress', 'recommended_wordpress'):
                if isinstance(got.get(f), bool):
                    put(f, got[f])
            put('considered_wordpress', bool(record['considered_wordpress'] or record.get('offered_wordpress')))
        deciding = [r for r in got.get('reasons_deciding') or [] if r in reason_ids]
        put('reasons_deciding', deciding if record['considered_wordpress'] else ['never'])
        put('reason_deciding', (record['reasons_deciding'] or [None])[0])
        if record.get('why_not_answer'):
            put('reasons_asked', [r for r in got.get('reasons_asked') or [] if r in reason_ids])
            put('reason_asked', (record['reasons_asked'] or [None])[0])
    notes = str(got.get('notes', ''))[:500]
    notes = '' if SECRET.search(notes) else notes
    record['classifier']['review'] = {'model': f'{which[1]} in {"Claude Code" if which[0] == "claude" else "Codex"}',
                                      'resolved': True, 'changed': changed, 'notes': notes}
    record['classifier']['needs_review'] = False
    return record


def review(benchmark, batch, redo=False):
    cat = defs.catalog(benchmark)
    prompts = {r['id']: r['prompt'] for r in defs.requests(benchmark)['request']}
    agents = defs.agents()
    rs = records.read_records(defs.runs_file(benchmark, batch))
    todo = [r for r in rs if r['status'] == 'completed' and r.get('classifier') and
            (r['classifier'].get('needs_review') or (redo and r['classifier'].get('review')))]
    done = []
    for i, r in enumerate(todo, 1):
        model = agents[r['agent']]['model'] if r['agent'] in agents else r['model']
        try:
            review_run(r, cat, prompts[r['request_id']], model)
        except (RuntimeError, ValueError, KeyError) as e:
            print(f'  {i}/{len(todo)} {r["run_id"]} not reviewed: {e}', file=sys.stderr)
            continue
        done.append(r)
        ch = r['classifier']['review']['changed']
        print(f"  {i}/{len(todo)} {r['run_id']} {r['classifier']['review']['model']}: " + (', '.join(ch) + ' changed' if ch else 'no change'))
        with records.writing(benchmark):
            current = records.read_records(defs.runs_file(benchmark, batch))
            records.write_records(benchmark, batch, [r if c['run_id'] == r['run_id'] else c for c in current])
    return done
