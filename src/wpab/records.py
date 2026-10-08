"""Turn Harbor job folders into run records: one JSON object per run, in data/<benchmark>/runs/<batch>.jsonl.

Records are appended as jobs are exported and never edited by hand. Every trial gets a record, including
ones that don't count, with a status saying why. See docs/data.md and schema/choose-run.schema.json.
"""
import contextlib
import fcntl
import json
import re
import threading
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator

from . import defs

SCHEMA_VERSION = '1.0'
# Commands that start a project on a platform, checked in order. Used when a run stalls before making files:
# the command it started shows the choice it had made.
SCAFFOLDS = [
    ('WordPress', r'wp core download|wp-cli|@wp-playground/cli|wp-env|wordpress:\S*|roots/bedrock|johnpbloch/wordpress'),
    ('Next.js', r'create-next-app|create next-app'),
    ('Astro', r'create[- ]astro'),
    ('Static site generator', r'create-docusaurus|create vitepress|@11ty|eleventy|hugo new site|jekyll new|mkdocs new|gatsby new'),
    ('Web framework', r'nuxi init|create-nuxt|create-remix|sv create|create-svelte|django-admin startproject|rails new|laravel new|laravel/laravel|create-t3-app'),
    ('Headless CMS', r'create-strapi|sanity init|create-payload-app|decap'),
    ('Shopify', r'shopify (theme|app) init|create-hydrogen'),
    ('Plain HTML or React', r'create[- ]vite|create-react-app'),
]
# Agents run in parallel, and other commands (classify, rebuild) may run at the same time from another
# terminal. One writer at a time, across threads and processes, keeps run IDs unique and no line is lost.
_THREAD_LOCK = threading.RLock()


@contextlib.contextmanager
def writing(benchmark):
    lock_path = defs.OUT / benchmark / 'runs' / '.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with _THREAD_LOCK, lock_path.open('w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
# Phrases harnesses print when a plan or API limit stops them. Such runs are retried, not counted.
LIMIT = re.compile(r"usage limit|rate limit(ed)?|limit reached|hit your (usage )?limit|quota (exceeded|exhausted)|resource.exhausted|too many requests", re.I)
CREDIT = re.compile(r'exceed your available credits|requires more credits|insufficient credits', re.I)


def read_records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def validator(benchmark):
    return Draft202012Validator(json.loads((defs.SCHEMA / f'{benchmark}-run.schema.json').read_text()))


def _json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _seconds(start, end):
    if not start or not end:
        return None
    parse = lambda s: datetime.fromisoformat(s.replace('Z', '+00:00'))
    return round((parse(end) - parse(start)).total_seconds(), 1)


def _answer(step_dir):
    """The agent's reply to the last thing it was asked in a step. A resumed session's trajectory holds the
    whole conversation, so this is everything the agent said after the last user message."""
    steps = (_json(step_dir / 'agent' / 'trajectory.json') or {}).get('steps', [])
    if not steps:
        return _stream_answer(step_dir)
    last_user = max((i for i, s in enumerate(steps) if s.get('source') == 'user'), default=-1)
    return '\n\n'.join(s['message'] for s in steps[last_user + 1:] if s.get('source') == 'agent' and s.get('message'))


def _stream_answer(step_dir):
    """For harnesses without a Harbor trajectory (Kimi Code): the assistant's text from the step's own JSON
    stream, which holds just that turn."""
    texts = []
    for log in sorted((step_dir / 'agent').glob('*.txt')):
        for line in log.read_text(errors='ignore').splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict) or event.get('role') != 'assistant':
                continue
            content = event.get('content')
            if isinstance(content, list):
                content = ''.join(c.get('text', '') for c in content if isinstance(c, dict))
            if isinstance(content, str) and content.strip():
                texts.append(content.strip())
    return '\n\n'.join(texts)


def _log_text(step_dir):
    """Everything the harness printed in a step, for spotting limit messages."""
    return '\n'.join(p.read_text(errors='ignore')[-20000:] for p in (step_dir / 'agent').glob('*.txt'))


def _scaffold_choice(step_dir):
    """The platform an agent started building with, from the first scaffolding command in its transcript."""
    text = ''
    traj = _json(step_dir / 'agent' / 'trajectory.json') or {}
    for s in traj.get('steps', []):
        for call in s.get('tool_calls') or []:
            text += '\n' + json.dumps(call.get('arguments'))
    for log in (step_dir / 'agent').glob('*stream*.jsonl'):
        text += '\n' + log.read_text(errors='ignore')
    hits = [(m.start(), name) for name, pattern in SCAFFOLDS for m in [re.search(pattern, text, re.I)] if m]
    return min(hits)[1] if hits else None


def _status(result, step, agent, step_dir):
    """completed, or why the run doesn't count."""
    exc = result.get('exception_info') or (step or {}).get('exception_info')
    logs = _log_text(step_dir) if step_dir.exists() else ''
    # A run that timed out still made its choice; it's counted as stalled (see choose_record).
    if (exc or {}).get('exception_type') == 'AgentTimeoutError' and (step or {}).get('verifier_result'):
        exc = None
    if LIMIT.search(json.dumps(exc) if exc else '') or (LIMIT.search(logs) and not (step or {}).get('verifier_result')):
        return 'limit_reached', 'The harness reported a usage or rate limit.'
    # Out of provider credit in any turn: the run didn't get to answer, so it isn't counted.
    turns = ' '.join(_log_text(d) for d in step_dir.parent.iterdir() if d.is_dir()) if step_dir.parent.exists() else logs
    if CREDIT.search(turns) or CREDIT.search(json.dumps(exc) if exc else ''):
        return 'limit_reached', 'The provider ran out of credit during the run.'
    if exc:
        return 'infra_error', f"{exc.get('exception_type', 'Error')}: {str(exc.get('exception_message', ''))[:300]}"
    if step is None or not step.get('verifier_result'):
        return 'infra_error', 'The first step has no verifier result.'
    usage = ((step.get('agent_result') or {}).get('model_usage') or {})
    expected = agent['model'].split('/')[-1]
    out = {m: (u or {}).get('n_output_tokens') or 0 for m, u in usage.items()}
    mine = sum(v for m, v in out.items() if m.split('/')[-1] == expected)
    if usage and (mine == 0 or mine < 0.5 * sum(out.values())):
        return 'model_switched', f'Most output came from {max(out, key=out.get)}, not {agent["model"]}.'
    return 'completed', None


def _chatgpt_site(step_dir):
    """Whether the agent told the person it published the site to a chatgpt.site address."""
    traj = _json(step_dir / 'agent' / 'trajectory.json') or {}
    return any(re.search(r'https://[\w.-]+\.chatgpt\.site', s.get('message') or '')
               for s in traj.get('steps', []) if s.get('source') == 'agent')


def _same_model(served, model):
    """Whether the model a harness says it served is the configured one (Cursor reports names like "Grok 4.7")."""
    norm = lambda m: re.sub(r'[^a-z0-9.]', '', m.split('/')[-1].split('[')[0].lower())
    return norm(served).startswith(norm(model))


def choose_record(job_dir, trial_dir, manifest, agent):
    """One Choosing run record from a Harbor trial folder, without run_id and batch."""
    result = _json(trial_dir / 'result.json') or {}
    request_id = Path((result.get('task_id') or {}).get('path', trial_dir.name.split('__')[0])).name
    req = next(r for r in defs.requests('choose')['request'] if r['id'] == request_id)
    kind = next(k for k in defs.catalog('choose')['kind'] if k['id'] == req['kind'])
    platforms = {p['name']: p for p in defs.catalog('choose')['platform']}
    steps = {s['step_name']: s for s in result.get('step_results') or []}
    first, step_dir = steps.get('request'), trial_dir / 'steps' / 'request'
    status, detail = _status(result, first, agent, step_dir)
    usage = (first or {}).get('agent_result') or {}
    facts = {**(_json(trial_dir / 'wpab.json') or {}), **(_json(step_dir / 'wpab.json') or {})}
    served = facts.get('served_model')
    if status == 'completed' and served and not _same_model(served, agent['model']):
        status, detail = 'model_switched', f'The harness served {served}, not {agent["model"]}.'
    choice = _json(step_dir / 'verifier' / 'choice.json') if status == 'completed' else None
    asked = trial_dir / 'steps' / 'why-not'
    considered_step = trial_dir / 'steps' / 'considered'
    platform = choice and choice['platform']
    stalled = bool(((first or {}).get('exception_info') or {}).get('exception_type') == 'AgentTimeoutError')
    if choice and stalled and platform == 'Nothing built':
        intended = _scaffold_choice(step_dir)
        if intended:
            platform, choice['evidence'] = intended, 'Stalled before making files; chose it by starting its scaffolding command'
    if choice:
        # Results from before the detector knew these cases, re-read from the files it listed.
        if any('/.openai/hosting' in '/' + f for f in choice.get('files', [])):
            platform, choice['evidence'] = 'ChatGPT site', 'Published to ChatGPT hosting (.openai/hosting.json)'
        elif _chatgpt_site(step_dir):
            platform, choice['evidence'] = 'ChatGPT site', 'Published to ChatGPT hosting (a chatgpt.site link)'
        elif platform == 'Other code' and choice['evidence'].startswith('Only documents'):
            platform, choice['evidence'] = 'Nothing built', 'Only notes or plans: ' + choice['evidence'].split(': ', 1)[-1]
    return {
        'schema_version': SCHEMA_VERSION,
        'benchmark': 'choose',
        # The request set the job ran with, not whatever is current when it's exported.
        'suite_version': manifest.get('suite_version') or defs.requests('choose')['version'],
        'request_id': request_id,
        'kind': kind['id'],
        'control': bool(kind.get('control')),
        'agent': agent['id'],
        'model': agent['model'],
        'harness': agent['harness'],
        'harness_version': manifest['agents'][agent['id']]['version'],
        'effort': manifest['agents'][agent['id']].get('effort'),
        'environment': manifest['agents'][agent['id']].get('environment'),
        'auth': manifest['auth'],
        'status': status,
        'status_detail': detail,
        'started_at': result.get('started_at'),
        'finished_at': result.get('finished_at'),
        'duration_s': _seconds(result.get('started_at'), result.get('finished_at')),
        'input_tokens': usage.get('n_input_tokens'),
        'cached_tokens': usage.get('n_cache_tokens'),
        'output_tokens': usage.get('n_output_tokens'),
        'cost_usd': usage.get('cost_usd') if manifest['auth'] == 'api' else None,
        'models_used': sorted((usage.get('model_usage') or {}).keys()),
        'nudged': facts.get('nudged'),
        'stalled': stalled,
        'built': None if choice is None else platform != 'Nothing built',
        'platform': platform,
        'platform_group': platforms[platform]['group'] if platform in platforms else None,
        'detection': None if choice is None else {'evidence': choice['evidence'], 'file_count': choice['file_count'],
                                                  'check_platform': None, 'check_confidence': None, 'agrees': None},
        'considered_wordpress': None,
        'offered_wordpress': None,
        'recommended_wordpress': None,
        'named_wordpress_unprompted': None,
        'reasons_deciding': [],
        'reasons_asked': [],
        'reason_deciding': None,
        'reason_asked': None,
        'considered_answer': (_answer(considered_step) or None) if considered_step.exists() and status == 'completed' else None,
        'why_not_answer': (_answer(asked) or None) if asked.exists() and status == 'completed' else None,
        'patterns': [],
        'classifier': None,
        'job': job_dir.name,
        'trial': trial_dir.name,
        'harbor_version': manifest.get('harbor_version'),
        'runner_commit': manifest.get('repo_commit'),
    }


def export(benchmark, batch, job_dirs):
    """Append a record for every trial in these jobs that isn't in the batch file yet. Returns the new records."""
    with writing(benchmark):
        return _export(benchmark, batch, job_dirs)


def _export(benchmark, batch, job_dirs):
    path = defs.runs_file(benchmark, batch)
    existing = read_records(path)
    seen = {(r['job'], r['trial']) for r in existing}
    check, new = validator(benchmark), []
    letter, yymm = benchmark[0].upper(), batch[2:4] + batch[5:7]
    for job_dir in sorted(job_dirs):
        manifest = _json(job_dir / 'wpab-manifest.json')
        if not manifest or manifest.get('benchmark') != benchmark or manifest.get('kind') == 'rerun':  # reruns never join a batch
            continue
        for trial_dir in sorted(p for p in job_dir.iterdir() if p.is_dir() and (p / 'result.json').exists()):
            if (job_dir.name, trial_dir.name) in seen:
                continue
            agent_id = next(iter(manifest['agents']))  # one agent per job
            record = choose_record(job_dir, trial_dir, manifest, defs.agents()[agent_id])
            # Local runs are marked, so their IDs never match a published run's.
            seq = f"{'L' if defs.local() else ''}{len(existing) + len(new) + 1:04d}"
            record = {'run_id': f'{letter}{yymm}-{seq}', 'batch': batch, **record}
            errors = sorted(check.iter_errors(record), key=str)
            if errors:
                raise ValueError(f'{trial_dir}: record fails the schema: {errors[0].message}')
            new.append(record)
    if new:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a') as f:
            for record in new:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
    return new


def write_records(benchmark, batch, records):
    """Rewrite a batch file in full, after classification. Every record is checked against the schema."""
    check = validator(benchmark)
    for record in records:
        errors = list(check.iter_errors(record))
        if errors:
            raise ValueError(f"{record['run_id']}: record fails the schema: {errors[0].message}")
    path = defs.runs_file(benchmark, batch)
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))


CLASSIFIED = ('considered_wordpress', 'offered_wordpress', 'recommended_wordpress', 'named_wordpress_unprompted', 'reasons_deciding', 'reasons_asked', 'reason_deciding', 'reason_asked', 'patterns', 'classifier')


def rebuild(benchmark, batch):
    """Re-derive every record in a batch from its saved job folder, with the current rules. Run IDs stay the
    same, and so does any classification. Records whose job folder is gone are kept as they are."""
    with writing(benchmark):
        path = defs.runs_file(benchmark, batch)
        old = read_records(path)
        out, changed = [], 0
        for r in old:
            job_dir, trial_dir = defs.JOBS / r['job'], defs.JOBS / r['job'] / r['trial']
            manifest = _json(job_dir / 'wpab-manifest.json')
            if not manifest or not (trial_dir / 'result.json').exists() or r['agent'] not in defs.agents():
                out.append(r)
                continue
            new = {'run_id': r['run_id'], 'batch': r['batch'], **choose_record(job_dir, trial_dir, manifest, defs.agents()[r['agent']])}
            new['suite_version'] = r.get('suite_version') or new['suite_version']  # what it ran with stays
            for k in CLASSIFIED:
                if r.get(k) not in (None, []):
                    new[k] = r[k]
            if new.get('detection') and (r.get('detection') or {}).get('check_platform'):
                new['detection'].update({k: r['detection'][k] for k in ('check_platform', 'check_confidence')})
                new['detection']['agrees'] = r['detection']['check_platform'] == new['platform']
            # A reviewer's decision on what was built outlasts a rebuild, like the classification does.
            settled = (((r.get('classifier') or {}).get('review') or {}).get('changed') or {})
            new.update({k: settled[k] for k in ('platform', 'platform_group') if k in settled})
            changed += new != r
            out.append(new)
        write_records(benchmark, batch, out)
        return changed
