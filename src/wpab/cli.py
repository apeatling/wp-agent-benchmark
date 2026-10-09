"""Run the benchmarks with Harbor and turn the results into run records.

    wpab doctor                              what's set up, and which agents you can run
    wpab try                                 one run with an agent you can run, to see how it works
    wpab run --agents grok-4-7-grok-build    this month's remaining runs for an agent
    wpab status --watch                      what's done and what's left this month, live
    wpab rerun C2610-0005                    one earlier run again, the same way
    wpab classify                            what each run said about WordPress, and why
    wpab site                                rebuild the site's data from the run records

Everything you run is local: runs, analysis and site data go to data/local/ and site/data-local/, which
are gitignored, so trying the benchmark never changes the published results. Maintainers add --publish
to write to data/ and site/data/ instead.

Signing in is automatic. An agent uses its maker's API key if it's set (see .env.example), otherwise your
own Claude or ChatGPT plan if you're signed in. Add :plan or :api to an agent ID, or --auth, to choose.
Settings are read from the environment and from a .env file in the repo root.
"""
import argparse
import collections
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from importlib.metadata import version
from pathlib import Path

from . import classify as classifier, deep, defs, insights as insight, progress, records, review as reviewer, site as sitedata

# Harbor from this same environment, so it can import our agent wrappers.
HARBOR = str(Path(sys.executable).with_name('harbor'))
API_ENV = {'anthropic': 'ANTHROPIC_API_KEY', 'openai': 'OPENAI_API_KEY', 'google': 'GEMINI_API_KEY',
           'openrouter': 'OPENROUTER_API_KEY', 'xai': 'XAI_API_KEY', 'moonshot': 'MOONSHOT_API_KEY'}


def load_dotenv():
    path = defs.ROOT / '.env'
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"\''))


def auth_env(auth, agent):
    """Check sign-in for one agent and return the environment for Harbor. Never logs the values."""
    env = dict(os.environ)
    # Agents talk to their makers' own services. A base URL inherited from the shell (a proxy, or the
    # environment of a tool this was started from) would change that, so it's dropped unless allowed.
    if not env.get('WPAB_ALLOW_BASE_URL'):
        for key in ('ANTHROPIC_BASE_URL', 'OPENAI_BASE_URL', 'GOOGLE_GEMINI_BASE_URL'):
            env.pop(key, None)
    if auth not in agent['auth']:
        sys.exit(f"{agent['id']} can't sign in with --auth {auth}. It supports: {', '.join(agent['auth'])}")
    if auth == 'plan':
        if agent['harness'] == 'claude-code':
            if not env.get('CLAUDE_CODE_OAUTH_TOKEN'):
                sys.exit('Missing CLAUDE_CODE_OAUTH_TOKEN (run `claude setup-token`)')
            env['CLAUDE_FORCE_OAUTH'] = '1'
        elif agent['harness'] == 'codex':
            if not env.get('CODEX_AUTH_JSON_PATH') and not (Path.home() / '.codex' / 'auth.json').exists():
                sys.exit('Missing a Codex login (run `codex login`)')
            env['CODEX_FORCE_AUTH_JSON'] = '1'
        elif agent['harness'] == 'cursor-cli':
            if not env.get('CURSOR_API_KEY'):
                sys.exit('Missing CURSOR_API_KEY (a user API key from cursor.com/dashboard, billed to your plan)')
        return env
    for key in ('CLAUDE_CODE_OAUTH_TOKEN', 'CLAUDE_FORCE_OAUTH', 'CODEX_AUTH_JSON_PATH', 'CODEX_FORCE_AUTH_JSON'):
        env.pop(key, None)
    # Open-weight models are reached through OpenRouter. Harnesses that only speak OpenAI's API, or their
    # own provider settings, are pointed at it with the OpenRouter key.
    if agent['harness'] == 'qwen-coder' and agent['model'].startswith('openrouter/'):
        if not env.get('OPENROUTER_API_KEY'):
            sys.exit(f"Missing OPENROUTER_API_KEY for {agent['id']}")
        env['OPENAI_API_KEY'], env['OPENAI_BASE_URL'] = env['OPENROUTER_API_KEY'], 'https://openrouter.ai/api/v1'
        return env
    if agent['harness'] == 'kimi-code':
        if not env.get('OPENROUTER_API_KEY'):
            sys.exit(f"Missing OPENROUTER_API_KEY for {agent['id']}")
        return env
    key = API_ENV.get(agent['model'].split('/')[0])
    if key and not env.get(key):
        sys.exit(f"Missing {key} for {agent['id']}")
    return env


def api_key(agent):
    """The environment variable holding the API key this agent needs."""
    if agent['harness'] in ('qwen-coder', 'kimi-code') or agent['model'].startswith('openrouter/'):
        return 'OPENROUTER_API_KEY'
    return API_ENV.get(agent['model'].split('/')[0])


PLAN_HOW = {'claude-code': 'a Claude plan: run `claude setup-token` and set CLAUDE_CODE_OAUTH_TOKEN',
            'codex': 'a ChatGPT plan: run `codex login`', 'cursor-cli': 'a Cursor plan: set CURSOR_API_KEY'}


PLAN_NAME = {'claude-code': 'your Claude plan', 'codex': 'your ChatGPT plan', 'cursor-cli': 'your Cursor plan'}


def plan_ready(agent):
    """Whether this machine is signed in to the agent's plan."""
    if 'plan' not in agent['auth']:
        return False
    if agent['harness'] == 'claude-code':
        return bool(os.environ.get('CLAUDE_CODE_OAUTH_TOKEN'))
    if agent['harness'] == 'codex':
        return bool(os.environ.get('CODEX_AUTH_JSON_PATH')) or (Path.home() / '.codex' / 'auth.json').exists()
    if agent['harness'] == 'cursor-cli':
        return bool(os.environ.get('CURSOR_API_KEY'))
    return False


def sign_in(agent):
    """How this agent will sign in without being told: its API key if set, otherwise a plan. None if neither."""
    key = api_key(agent)
    if 'api' in agent['auth'] and key and os.environ.get(key):
        return 'api'
    return 'plan' if plan_ready(agent) else None


def sign_in_help(agent):
    """What to set up so this agent can run."""
    ways = [f"set {api_key(agent)}"] if 'api' in agent['auth'] and api_key(agent) else []
    if 'plan' in agent['auth']:
        ways.append('use ' + PLAN_HOW.get(agent['harness'], 'your plan'))
    return ' or '.join(ways)


def remaining(benchmark, batch, agent_id, repeats):
    """Requests this agent still needs this batch, fewest done first. Only completed runs count."""
    done = collections.Counter(r['request_id'] for r in records.read_records(defs.runs_file(benchmark, batch))
                               if r['agent'] == agent_id and r['status'] == 'completed')
    reqs = [r['id'] for r in defs.requests(benchmark)['request']]
    return sorted((r for r in reqs if done[r] < repeats), key=lambda r: (done[r], reqs.index(r)))


# Your own prompts have no kind of site; they're never counted in any results.
OWN_KIND = {'id': 'own', 'name': 'Your own prompt'}
BENCH_NAME = {'choose': 'Choosing WordPress', 'build': 'Building with WordPress'}
STATUS = {'completed': 'completed', 'infra_error': 'errors (not counted)', 'limit_reached': 'hit a usage limit (not counted)',
          'model_switched': 'switched model (not counted)'}


def header(printer, benchmark, batch, picked, queue):
    """What's about to run: each agent, how it signs in, and how many runs are queued."""
    where = 'local runs, in data/local/' if defs.local() else 'published runs, in data/'
    printer.line(f"{BENCH_NAME[benchmark]}, {batch} batch, {where}. Harbor's detailed output is in each job's harbor.log.")
    for agent, auth in picked:
        printer.line(f"  {agent['name'] + ' in ' + agent['harness_name']:<32} {auth:<5} {len(queue[agent['id']]):>3} queued")


def summary(printer, benchmark, batch, picked, repeats):
    """One line: each agent's completed runs for the batch and what's left."""
    target = len(defs.requests(benchmark)['request']) * repeats
    parts = []
    for agent, _ in picked:
        done = sum(1 for r in records.read_records(defs.runs_file(benchmark, batch)) if r['agent'] == agent['id'] and r['status'] == 'completed')
        parts.append(f"{agent['name']} {min(done, target)}/{target}")
    printer.line('Batch so far: ' + ', '.join(parts), progress.DIM)


def cleanup(job_dir):
    """Remove the Docker images and networks Harbor made for this job's runs. Harbor builds one image per run
    (named after the trial) and leaves it behind; a month's batch would otherwise leave hundreds."""
    if not job_dir.exists():
        return
    for trial in (p.name.lower() for p in job_dir.iterdir() if p.is_dir()):
        subprocess.run(['docker', 'image', 'rm', '-f', f'{trial}__env-main'], capture_output=True)
        subprocess.run(['docker', 'network', 'rm', f'{trial}__env_default'], capture_output=True)


def run_agent(benchmark, batch, agent, auth, todo, concurrent=3, env_type='docker', printer=None, plan_concurrent=1):
    """One Harbor job: these requests, for one agent. Exports the records and returns their statuses."""
    kind = 'local' if defs.local() else 'published'
    job_dir = harbor_job(benchmark, batch, agent, auth, todo, kind, concurrent, env_type, printer, plan_concurrent)
    if not job_dir:
        return collections.Counter({'infra_error': len(todo)})
    return collections.Counter(r['status'] for r in records.export(benchmark, batch, [job_dir]))


def harbor_job(benchmark, batch, agent, auth, todo, kind, concurrent=3, env_type='docker', printer=None, plan_concurrent=1, extra=None,
               tasks_dir=None, attempts=1):
    """Run these requests for one agent in a Harbor job. Returns the job folder, or None if Harbor made nothing.
    tasks_dir: where the tasks are, if not tasks/<benchmark>/<environment> (your own prompts are built elsewhere)."""
    tasks_dir = tasks_dir or defs.ROOT / 'tasks' / benchmark / agent['environment']
    env = auth_env(auth, agent)
    when = datetime.datetime.now(datetime.timezone.utc)
    job = f"{kind}-{benchmark}-{agent['id']}-{when:%Y%m%d-%H%M%S}"
    # Only published jobs can become published records; see export.
    extra = {'publish': kind == 'published', **(extra or {})}
    # Plans run one at a time, so the runs look like one person working, not a burst.
    concurrent = plan_concurrent if auth == 'plan' else concurrent
    kwargs = {} if agent['version'] == 'TODO' else {'version': agent['version']}
    if agent.get('effort'):
        kwargs['reasoning_effort'] = agent['effort']
    config = {
        'job_name': job, 'jobs_dir': str(defs.JOBS), 'n_attempts': attempts, 'n_concurrent_trials': concurrent,
        'environment': {'type': env_type, 'delete': True},
        'agents': [{'import_path': agent['import_path'], 'model_name': agent['model'], 'resume_trajectory': True, 'kwargs': kwargs}],
        'tasks': [{'path': str(tasks_dir / t)} for t in todo],
    }
    manifest = {
        'job': job, 'kind': kind, 'auth': auth, 'benchmark': benchmark, 'batch': batch, 'tasks': todo,
        'started': when.isoformat(), 'environment': env_type,
        'agents': {agent['id']: {'harness': agent['harness'], 'version': agent['version'], 'model': agent['model'], 'effort': agent.get('effort'),
                                 'environment': agent['environment']}},
        'harbor_version': version('harbor'), 'repo_commit': defs.git_commit(),
        'suite_version': defs.requests(benchmark)['version'], **extra,
    }
    defs.JOBS.mkdir(exist_ok=True)
    config_path = defs.JOBS / f'{job}.config.json'
    config_path.write_text(json.dumps(config, indent=2))
    # Harbor's detailed output goes to a log next to the job; the terminal gets one line per finished run.
    harbor_log = defs.JOBS / f'{job}.harbor.log'
    stop = threading.Event()
    watcher = threading.Thread(target=progress.watch, args=(job, agent, printer, stop)) if printer else None
    if watcher:
        watcher.start()
    with harbor_log.open('w') as out:
        code = subprocess.run([HARBOR, 'run', '-c', str(config_path)], cwd=defs.ROOT, env=env, stdout=out, stderr=out).returncode
    stop.set()
    if watcher:
        watcher.join()
    job_dir = defs.JOBS / job
    if job_dir.exists():
        if harbor_log.exists():  # another wpab process's start-up recovery may have moved it already
            harbor_log.rename(job_dir / 'harbor.log')
    cleanup(job_dir)
    if not job_dir.exists():
        return None
    manifest['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest['harbor_exit'] = code
    (job_dir / 'wpab-manifest.json').write_text(json.dumps(manifest, indent=2))
    config_path.rename(job_dir / 'wpab-config.json')
    return job_dir


def preflight(env_type):
    """Check the machine can run sandboxes before starting, rather than failing every run."""
    if env_type != 'docker':
        return
    if subprocess.run(['docker', 'info'], capture_output=True).returncode:
        sys.exit('Docker isn\'t running. Start Docker Desktop and try again.')
    name = f'wpab-preflight-{os.getpid()}'
    made = subprocess.run(['docker', 'network', 'create', name], capture_output=True, text=True)
    if made.returncode:
        sys.exit('Docker can\'t create a network for the sandboxes: ' + made.stderr.strip()[:200] +
                 '\nUsually there are too many old networks. Remove unused ones with: docker network prune -f')
    subprocess.run(['docker', 'network', 'rm', name], capture_output=True)
    free = shutil.disk_usage(defs.ROOT).free / 1e9
    if free < 10:
        sys.exit(f'Only {free:.0f} GB of disk is free; runs need room for images. Free some space (for example: docker image prune) and try again.')


def recover(benchmark, batch, printer=None):
    """Keep the work of jobs that were stopped (Ctrl-C, a crash, a restart): write the manifest they never
    got from the config the runner left, record their finished runs, then apply the current rules to every
    record. Only safe when nothing else is running, so it's called before runs start."""
    found = 0
    for cfg in sorted(defs.JOBS.glob(f'*-{benchmark}-*.config.json')) if defs.JOBS.exists() else []:
        job = defs.JOBS / cfg.name.removesuffix('.config.json')
        agent = next((a for a in defs.agents().values() if f"-{a['id']}-" in job.name), None)
        mine = job.name.startswith('local-') if defs.local() else job.name.startswith(('published-', 'official-'))
        if not job.is_dir() or not agent or (job / 'wpab-manifest.json').exists() or not mine:
            continue
        config = json.loads(cfg.read_text())
        (job / 'wpab-manifest.json').write_text(json.dumps({
            'job': job.name, 'kind': 'local' if defs.local() else 'published', 'publish': not defs.local(), 'benchmark': benchmark, 'batch': batch,
            'auth': 'api' if agent['auth'] == ['api'] else 'plan', 'interrupted': True,
            'agents': {agent['id']: {'harness': agent['harness'], 'version': agent['version'], 'model': agent['model'],
                                     'effort': agent.get('effort'), 'environment': agent['environment']}},
            'tasks': [Path(t['path']).name for t in config.get('tasks', [])],
            'harbor_version': version('harbor'), 'repo_commit': defs.git_commit(),
            'suite_version': defs.requests(benchmark)['version']}, indent=2))
        cfg.rename(job / 'wpab-config.json')
        harbor_log = defs.JOBS / f'{job.name}.harbor.log'
        if harbor_log.exists():
            harbor_log.rename(job / 'harbor.log')
        found += len(records.export(benchmark, batch, [job]))
        cleanup(job)
    records.rebuild(benchmark, batch)
    if printer and found:
        printer.line(f'Recovered {found} runs from stopped jobs.')


def pick_agents(spec, default_auth=None):
    """Agents from a comma-separated list. Each signs in automatically (see sign_in), unless it names a way,
    e.g. opus-5-5-claude-code:plan, or --auth sets one for all."""
    if not spec:
        sys.exit('Choose agents with --agents. Run `wpab doctor` to see the ones you can run.')
    picked = []
    for item in spec.split(','):
        agent_id, _, auth = item.partition(':')
        if agent_id not in defs.agents():
            sys.exit(f'No agent {agent_id}. Run `wpab doctor` to see the agents and which you can run.')
        agent = defs.agents()[agent_id]
        auth = auth or default_auth or sign_in(agent)
        if not auth:
            sys.exit(f"{agent['name']} in {agent['harness_name']} can't sign in: {sign_in_help(agent)}.")
        picked.append((agent, auth))
    return picked


def estimate(benchmark, picked, queue, concurrent, plan_concurrent):
    """Rough cost and time for the queued runs, from the published runs so far. Plan runs cost nothing extra."""
    past = collections.defaultdict(list)
    for path in sorted((defs.DATA / benchmark / 'runs').glob('*.jsonl')):
        for r in records.read_records(path):
            if r['status'] == 'completed':
                past[r['agent']].append(r)
    cost, minutes, unknown = 0.0, 0.0, []
    for agent, auth in picked:
        n, mine = len(queue[agent['id']]), past[agent['id']]
        if not n:
            continue
        if mine:
            per = sorted(r['duration_s'] for r in mine)[len(mine) // 2] / 60
            minutes = max(minutes, per * n / (plan_concurrent if auth == 'plan' else concurrent))
        priced = sorted(r['cost_usd'] for r in mine if r['cost_usd'] is not None)
        if auth == 'api':
            if priced:
                cost += priced[len(priced) // 2] * n
            else:
                unknown.append(agent['name'])
    return cost, minutes, unknown


def confirm(benchmark, picked, queue, args):
    """Say what a run will take before starting it, and ask first if it's more than a few runs."""
    total = sum(len(q) for q in queue.values())
    cost, minutes, unknown = estimate(benchmark, picked, queue, args.concurrent, args.plan_concurrent)
    line = f"{total} {'run' if total == 1 else 'runs'}, about {max(1, round(minutes))} {'minute' if round(minutes) <= 1 else 'minutes'}"
    if cost:
        line += f", about ${cost:.2f} in API costs"
    if unknown:
        line += f" (no cost history for {', '.join(unknown)})"
    print(line + ('. Plan runs use your plan’s allowance.' if any(a == 'plan' for _, a in picked) else '.'))
    if total > 5 and not args.yes and sys.stdin.isatty():
        if input('Start? [y/N] ').strip().lower() not in ('y', 'yes'):
            sys.exit('Not started. Use --runs to do fewer, or -y to skip this question.')


def run(args):
    benchmark, batch = args.benchmark, args.batch
    picked = pick_agents(args.agents, args.auth)
    for agent, auth in picked:
        if agent['version'] == 'TODO' and not defs.local():
            sys.exit(f"{agent['id']} has no pinned version in benchmarks/agents.toml, so its runs can't be published.")
        auth_env(auth, agent)  # fail before running anything if sign-in is missing
    preflight(args.env)
    recover(benchmark, batch)
    queue = {agent['id']: remaining(benchmark, batch, agent['id'], args.repeats)[:args.runs] for agent, _ in picked}
    confirm(benchmark, picked, queue, args)
    defs.JOBS.mkdir(exist_ok=True)
    printer = progress.Printer(defs.JOBS / f"run-{benchmark}-{datetime.datetime.now():%Y%m%d-%H%M}.log")
    header(printer, benchmark, batch, picked, queue)

    # Every agent runs at the same time, each with its own Harbor job; --concurrent is runs at once per agent.
    def one(agent, auth):
        todo = queue[agent['id']]
        if not todo:
            return
        printer.total[agent['id']] = len(todo)
        stats = run_agent(benchmark, batch, agent, auth, todo, args.concurrent, args.env, printer, args.plan_concurrent)
        printer.line(f"{agent['name']}: " + ', '.join(f'{n} {STATUS[s]}' for s, n in stats.items()))
        if auth == 'plan' and stats.get('limit_reached'):
            printer.line(f"{agent['name']}: hit a usage limit. Run again later; those requests will be picked again.", progress.YELLOW)

    threads = [threading.Thread(target=one, args=pair, name=pair[0]['id']) for pair in picked]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return 0


def find_run(benchmark, run_id):
    """A run record by ID, from any batch, published or local."""
    for path in sorted((defs.DATA / benchmark / 'runs').glob('*.jsonl')) + sorted((defs.LOCAL_OUT / benchmark / 'runs').glob('*.jsonl')):
        for r in records.read_records(path):
            if r['run_id'] == run_id:
                return r
    sys.exit(f'No run {run_id} in data/{benchmark}/runs/ or data/local/{benchmark}/runs/.')


def rerun(args):
    """Run one request again with the agent, version, model, settings and sandbox an earlier run used. The new
    run is kept in its own job folder and never added to a batch, so it doesn't change any results."""
    old = find_run(args.benchmark, args.run_id)
    if old['agent'] not in defs.agents():
        sys.exit(f"{old['agent']} is no longer in benchmarks/agents.toml, so its harness can't be set up.")
    suite = defs.requests(args.benchmark)['version']
    if old['suite_version'] != suite:
        sys.exit(f"{args.run_id} used requests version {old['suite_version']}; this checkout has {suite}. "
                 f"Check out the commit it ran from ({old['runner_commit'].removesuffix('-dirty')}) and try again.")
    # The agent as it was for that run, not as it's set up today.
    agent = {**defs.agents()[old['agent']], 'version': old['harness_version'] or 'TODO', 'model': old['model'],
             'effort': old['effort'], 'environment': old['environment']}
    auth = args.auth or old['auth']
    auth_env(auth, agent)
    preflight(args.env)
    printer = progress.Printer(defs.JOBS / f"rerun-{args.run_id}-{datetime.datetime.now():%Y%m%d-%H%M}.log")
    printer.line(f"Re-running {args.run_id}: {old['request_id']}, {agent['name']} in {agent['harness_name']} {old['harness_version']}, "
                 f"{old['environment']}, {auth}.")
    if old['runner_commit'] != defs.git_commit():
        printer.line(f"It ran from commit {old['runner_commit']}; this is {defs.git_commit()}. The harness wrappers may differ.", progress.YELLOW)
    printer.total[agent['id']] = 1
    job_dir = harbor_job(args.benchmark, None, agent, auth, [old['request_id']], 'rerun', env_type=args.env, printer=printer,
                         extra={'rerun_of': args.run_id, 'publish': False})
    trials = sorted(p for p in job_dir.iterdir() if p.is_dir() and (p / 'result.json').exists()) if job_dir else []
    if not trials:
        printer.line('The rerun produced no result. See the job\'s harbor.log.', progress.YELLOW)
        return 1
    new = records.choose_record(job_dir, trials[0], json.loads((job_dir / 'wpab-manifest.json').read_text()), agent)
    printer.line(f"Then:  {old['status']}, built with {old['platform']}")
    printer.line(f"Now:   {new['status']}, built with {new['platform']}")
    printer.line(f'Job folder: {job_dir.relative_to(defs.ROOT)}', progress.DIM)
    return 0


def overnight(args):
    """Run every agent's remaining requests unattended, in parallel, then classify and rebuild the site."""
    benchmark, batch = args.benchmark, args.batch
    picked = pick_agents(args.agents)
    for agent, auth in picked:
        auth_env(auth, agent)  # check every sign-in before starting
    preflight(args.env)
    recover(benchmark, batch)
    now = datetime.datetime.now()
    stop = datetime.datetime.combine(now.date(), datetime.time.fromisoformat(args.until))
    stop += datetime.timedelta(days=1) if stop <= now else datetime.timedelta()
    log_path = defs.JOBS / f"overnight-{benchmark}-{now:%Y%m%d-%H%M}.log"
    defs.JOBS.mkdir(exist_ok=True)
    printer = progress.Printer(log_path)
    log = printer.line
    queue = {agent['id']: remaining(benchmark, batch, agent['id'], args.repeats) for agent, _ in picked}
    # Counts on each finished run are against the whole batch, since agents loop until every request has its repeats.
    target = len(defs.requests(benchmark)['request']) * args.repeats
    for agent, _ in picked:
        printer.total[agent['id']] = target
        printer.done[agent['id']] = sum(1 for r in records.read_records(defs.runs_file(benchmark, batch))
                                        if r['agent'] == agent['id'] and r['status'] == 'completed')

    # Keep the Mac awake while this process runs.
    if sys.platform == 'darwin':
        subprocess.Popen(['caffeinate', '-i', '-w', str(os.getpid())])

    def work(agent, auth):
        failures = 0
        while True:
            todo = remaining(benchmark, batch, agent['id'], args.repeats)
            if not todo:
                return log(f"{agent['name']}: finished all its runs", progress.GREEN)
            if datetime.datetime.now() >= stop:
                return log(f"{agent['name']}: stopped at {args.until} with {len(todo)} requests left", progress.YELLOW)
            # Plans go a few at a time, so a usage limit stops them after one short job.
            chunk = todo[:max(args.plan_chunk, args.plan_concurrent)] if auth == 'plan' else todo
            stats = run_agent(benchmark, batch, agent, auth, chunk, concurrent=args.concurrent, env_type=args.env, printer=printer,
                              plan_concurrent=args.plan_concurrent)
            if stats.get('limit_reached'):
                wake = min(stop, datetime.datetime.now() + datetime.timedelta(minutes=args.wait))
                log(f"{agent['name']}: usage limit, waiting until {wake:%H:%M}", progress.YELLOW)
                time.sleep(max(0, (wake - datetime.datetime.now()).total_seconds()))
            failures = failures + 1 if not stats.get('completed') else 0
            if failures >= 3:
                return log(f"{agent['name']}: stopped after 3 jobs in a row with no completed runs. Check the harbor.log in its latest job.", progress.RED)

    header(printer, benchmark, batch, picked, queue)
    log(f"Running until {stop:%a %H:%M}. Follow along from another terminal: tail -f {os.path.relpath(log_path)}")
    threads = [threading.Thread(target=work, args=pair) for pair in picked]
    for t in threads:
        t.start()
    # Every 10 minutes, one line on where the batch stands.
    while any(t.is_alive() for t in threads):
        for t in threads:
            t.join(timeout=600 / len(threads))
        if any(t.is_alive() for t in threads):
            summary(printer, benchmark, batch, picked, args.repeats)
    summary(printer, benchmark, batch, picked, args.repeats)
    done = classifier.classify(benchmark, batch)
    log(f"Classified {len(done)} runs with {classifier.who()}, {sum(r['classifier']['needs_review'] for r in done)} flagged for review")
    reviewed = reviewer.review(benchmark, batch)
    log(f"Reviewed {len(reviewed)} flagged runs with a second model, {sum(bool(r['classifier']['review']['changed']) for r in reviewed)} changed")
    data = sitedata.build(benchmark, batch)
    log(f"Site data rebuilt: {len(data['runs'])} runs. Next: `wpab insights {benchmark}`, review the draft, then `wpab site {benchmark}`.")
    return 0


def export(args):
    if args.rebuild:
        n = records.rebuild(args.benchmark, args.batch)
        print(f'{n} records updated from their job folders with the current rules.')
        return 0
    jobs = [p for p in defs.JOBS.iterdir() if p.is_dir()] if defs.JOBS.exists() else []
    def wanted(job):
        m = json.loads((job / 'wpab-manifest.json').read_text())
        # Jobs from before local runs existed have no 'publish' and were all published.
        return m.get('batch') == args.batch and m.get('publish', True) is not defs.local() and m.get('kind') not in ('rerun', 'try')
    jobs = [j for j in jobs if (j / 'wpab-manifest.json').exists() and wanted(j)]
    new = records.export(args.benchmark, args.batch, jobs)
    print(f'{len(new)} records added to {defs.runs_file(args.benchmark, args.batch).relative_to(defs.ROOT)}')


def classify(args):
    done = classifier.classify(args.benchmark, args.batch, redo=args.redo)
    review = sum(1 for r in done if r['classifier']['needs_review'])
    print(f'{len(done)} runs classified with {classifier.who()}, {review} flagged for review. Next: `wpab review`.')


def review(args):
    done = reviewer.review(args.benchmark, args.batch, redo=args.redo)
    changed = sum(1 for r in done if r['classifier']['review']['changed'])
    print(f'{len(done)} flagged runs reviewed, {changed} changed.')


def insights(args):
    path = insight.draft(args.batch)
    print(f'Draft written to {path.relative_to(defs.ROOT)}. Review and edit it, then save it as {path.name.replace(".draft", "")} and run `wpab site`.')


def analyse(args):
    runs = deep.extract(args.batch)
    grouped = deep.group(args.batch)
    deep.check_claims(args.batch)
    print(f"{len(runs)} runs read: {len(grouped['claims'])} claims and {len(grouped['conditions'])} conditions, checked against the facts. Next: `wpab advise {args.benchmark}`.")


def advise(args):
    # The free-form draft (advice.md), checked, then split into the page's parts without losing a line.
    out = deep.write(args.batch)
    checks = deep.check_advice(args.batch)
    parts = deep.sections(args.batch)
    recs = sum(1 for s in parts['sections'] if s['recommendation'])
    print(f"{recs} recommendations in {out.relative_to(defs.ROOT)}. Quotes checked {checks['quotes_checked']}, "
          f"not found {checks['quotes_not_found']}; links not in sources {checks['links_not_in_sources']}; "
          f"opening {checks['opening_words']} words. Next: `wpab site choose`.")


def site(args):
    if not defs.runs_file(args.benchmark, args.batch).exists():
        sys.exit(f"No runs for {args.batch} in {defs.runs_file(args.benchmark, args.batch).parent.relative_to(defs.ROOT)}/ yet. "
                 "Run some agents with `wpab run` first (`wpab try` runs aren't added to any results).")
    data = sitedata.build(args.benchmark, args.batch)
    out = defs.SITE_DATA.relative_to(defs.ROOT)
    print(f"{out}/{args.benchmark}.json: {len(data['runs'])} runs from {len(data['agents'])} agents, batch {args.batch}. "
          + ('View it with `uv run python scripts/serve.py --local`.' if defs.local() else ''))


def local(iso, fmt='%b %d %H:%M'):
    """A record's UTC timestamp in this machine's time."""
    if not iso:
        return ''
    return datetime.datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone().strftime(fmt)


def analysis_lines(args, rs):
    """Where the batch's analysis stands: classified, reviewed, insights drafted, site data built."""
    done = [r for r in rs if r['status'] == 'completed']
    if not done:
        return []
    classified = [r for r in done if r.get('classifier')]
    reviewed = [r for r in classified if r['classifier'].get('review')]
    waiting = [r for r in classified if r['classifier'].get('needs_review')]
    insights = defs.OUT / args.benchmark / 'insights'
    if (insights / f'{args.batch}.json').exists():
        drafted = 'reviewed and saved'
    elif (insights / f'{args.batch}.draft.json').exists():
        drafted = f"draft ready for review ({local(datetime.datetime.fromtimestamp((insights / f'{args.batch}.draft.json').stat().st_mtime, datetime.timezone.utc).isoformat())})"
    else:
        drafted = f'not drafted yet (wpab insights {args.benchmark})'
    data = defs.SITE_DATA / f'{args.benchmark}.json'
    built = json.loads(data.read_text()) if data.exists() else {}
    fresh = data.exists() and (built.get('batch') or {}).get('id') == args.batch and len(built.get('runs', [])) == len(done) and \
        data.stat().st_mtime >= defs.runs_file(args.benchmark, args.batch).stat().st_mtime
    site = (f"built {local(datetime.datetime.fromtimestamp(data.stat().st_mtime, datetime.timezone.utc).isoformat())}, {len(built.get('runs', []))} runs"
            + ('' if fresh else f' (out of date: wpab site {args.benchmark})')) if data.exists() else f'not built (wpab site {args.benchmark})'
    return ['', 'Analysis:',
            f"  {'Classified':<14} {len(classified)}/{len(done)}" + ('' if len(classified) == len(done) else f'  (wpab classify {args.benchmark})'),
            f"  {'Reviewed':<14} {len(reviewed)} of {len(reviewed) + len(waiting)} flagged" + (f', {len(waiting)} waiting' if waiting else ''),
            f"  {'Insights':<14} {drafted}",
            f"  {'Site data':<14} {site}"]


def status_lines(args):
    """The batch as a table, then runs in progress and the latest results."""
    rs = records.read_records(defs.runs_file(args.benchmark, args.batch))
    reqs = defs.requests(args.benchmark)['request']
    target = len(reqs) * args.repeats
    where = 'Your local runs (data/local/); add --publish for the published ones.' if defs.local() else 'Published runs (data/).'
    out = [f"{BENCH_NAME[args.benchmark]}, {args.batch} batch. Target: {target} completed runs per agent ({len(reqs)} requests x {args.repeats}).", where, '',
           f"  {'Agent':<32} {'Completed':>10} {'Not counted':>12} {'Left':>6}   Last run"]
    # Runs that finished in jobs still going: counted now, recorded when the job ends.
    pending = collections.Counter()
    for job in (defs.JOBS.glob(f'*-{args.benchmark}-*') if defs.JOBS.exists() else []):
        if job.is_dir() and not (job / 'wpab-manifest.json').exists():
            agent = next((a for a in defs.agents().values() if f"-{a['id']}-" in job.name), None)
            for t in job.iterdir():
                if agent and t.is_dir() and (t / 'steps' / 'request' / 'verifier' / 'choice.json').exists():
                    pending[agent['id']] += 1
    for agent in defs.agents().values():
        mine = [r for r in rs if r['agent'] == agent['id']]
        if not mine and not pending[agent['id']]:
            continue
        recorded = sum(r['status'] == 'completed' for r in mine)
        done = recorded + pending[agent['id']]
        counts = collections.Counter(r['request_id'] for r in mine if r['status'] == 'completed')
        left = max(0, sum(max(0, args.repeats - counts[q['id']]) for q in reqs) - pending[agent['id']])
        last = local(max(r['finished_at'] or r['started_at'] for r in mine)) if mine else 'running'
        out.append(f"  {agent['name'] + ' in ' + agent['harness_name']:<32} {min(done, target):>6}/{target:<3} {len(mine) - recorded:>12} {left:>6}   {last}")
    # Runs in progress: trials in jobs that haven't finished, with the step they're on.
    now = datetime.datetime.now(datetime.timezone.utc)
    running = []
    for job in (sorted(defs.JOBS.glob(f'*-{args.benchmark}-*')) if defs.JOBS.exists() else []):
        if not job.is_dir() or (job / 'wpab-manifest.json').exists():
            continue
        agent = next((a for a in defs.agents().values() if f"-{a['id']}-" in job.name), None)
        for t in sorted(p for p in job.iterdir() if p.is_dir()):
            result = records._json(t / 'result.json') or {}
            if result.get('finished_at'):
                continue
            # A trial nothing has written to for 30 minutes was abandoned (its run was stopped), not running.
            if (t / 'exception.txt').exists() or now.timestamp() - max((f.stat().st_mtime for f in t.rglob('*') if f.is_file()), default=0) > 1800:
                continue
            step = 'asking why not WordPress' if (t / 'steps' / 'why-not').exists() else 'building'
            st = t.stat()  # when the trial's folder was created, which is when the run began
            mins = int((now.timestamp() - getattr(st, 'st_birthtime', st.st_ctime)) // 60)
            running.append(f"  {(agent['name'] if agent else job.name):<16} {t.name.split('__')[0]:<12} {step:<26} {mins}m")
    out += analysis_lines(args, rs)
    out += ['', 'Running now:'] + (running or ['  nothing'])
    latest = sorted(rs, key=lambda r: r['finished_at'] or r['started_at'])[-5:]
    if latest:
        out += ['', 'Latest:']
        for r in reversed(latest):
            name = defs.agents()[r['agent']]['name'] if r['agent'] in defs.agents() else r['agent']
            what = r['platform'] if r['status'] == 'completed' else STATUS[r['status']]
            out.append(f"  {local(r['finished_at'] or r['started_at'], '%H:%M')}  {name:<16} {r['request_id']:<12} {what}")
    return out


def status(args):
    if not args.watch:
        print('\n'.join(status_lines(args)))
        return 0
    try:
        while True:
            # Clear the screen and redraw, so the view stays in place.
            print('\033[2J\033[H' + '\n'.join(status_lines(args)) + f"\n\nUpdated {datetime.datetime.now():%H:%M:%S}. Ctrl-C to stop.", flush=True)
            time.sleep(args.every)
    except KeyboardInterrupt:
        return 0


def doctor(args):
    """What's set up on this machine, and the agents it can run, with the command to try each."""
    ok, warn, bad = progress.GREEN + 'ok' + progress.RESET, progress.YELLOW + '--' + progress.RESET, progress.RED + '!!' + progress.RESET
    print('Machine')
    docker = shutil.which('docker') and not subprocess.run(['docker', 'info'], capture_output=True).returncode
    print(f"  {ok if docker else bad}  Docker {'is running' if docker else 'isn’t running. Install Docker Desktop and start it; every run happens in a container.'}")
    free = shutil.disk_usage(defs.ROOT).free / 1e9
    print(f"  {ok if free >= 20 else bad}  {free:.0f} GB free disk{'' if free >= 20 else '. Runs need room for images (the Codex one alone is several GB).'}")
    for cli, why in (('claude', 'classifying runs without a TypeSafe key, and the analysis'), ('codex', 'reviewing the Claude agents’ runs in the analysis')):
        found = shutil.which(cli)
        print(f"  {ok if found else warn}  {cli} CLI {'found' if found else 'not found'}: used for {why}")
    print(f"  {ok if os.environ.get('TYPESAFE_API_KEY') else warn}  Classifying runs: "
          + ('Jev, with TYPESAFE_API_KEY' if os.environ.get('TYPESAFE_API_KEY') else 'no TYPESAFE_API_KEY, so the claude CLI does it on your Claude plan'))
    print("\nAgents (sign-in is automatic: an API key if set, otherwise your plan)")
    ready = []
    for agent in defs.agents().values():
        how = sign_in(agent)
        label = f"{agent['name']} in {agent['harness_name']}"
        if how:
            ready.append(agent)
            via = f"API key, {api_key(agent)}" if how == 'api' else PLAN_NAME.get(agent['harness'], 'your plan')
            print(f"  {ok}  {label:<34} {agent['id']:<34} {via}")
        else:
            print(f"  {warn}  {label:<34} {agent['id']:<34} {sign_in_help(agent)}")
    print()
    if not docker:
        print('Start Docker, then run `uv run wpab doctor` again.')
    elif ready:
        print(f"Next: `uv run wpab try {ready[0]['id']}` for one run, or `uv run wpab run --agents {ready[0]['id']}` for this month’s runs.")
    else:
        print('Next: add a key to .env (see .env.example; OPENROUTER_API_KEY alone covers five agents), then run this again.')
    return 0


CUSTOM_TASKS = defs.ROOT / 'data' / 'local' / 'custom-tasks'


def own_prompt(prompt, agent):
    """A one-off Choosing task for a prompt of your own, built like the published ones and kept in
    data/local/custom-tasks/ (gitignored). Returns the request and the folder its task is in."""
    spec = importlib.util.spec_from_file_location('build_tasks', defs.ROOT / 'scripts' / 'build_tasks.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    req = {'id': 'own-' + hashlib.sha256(prompt.encode()).hexdigest()[:8], 'kind': 'own', 'prompt': prompt}
    env = defs.environments()[agent['environment']]
    folder = CUSTOM_TASKS / env['id']
    if not (folder / req['id']).exists():
        folder.mkdir(parents=True, exist_ok=True)
        builder.build_request(folder / req['id'], env, req, OWN_KIND, defs.requests('choose')['version'])
    return req, folder


def try_one(args):
    """One run of one request, to see how the benchmark works. Kept in its own job folder; never part of a batch."""
    if args.agent:
        agent, auth = pick_agents(args.agent, args.auth)[0]
    else:
        ready = [a for a in defs.agents().values() if sign_in(a)]
        if not ready:
            sys.exit('No agent can sign in yet. Run `uv run wpab doctor` to see what to set up.')
        agent, auth = ready[0], args.auth or sign_in(ready[0])
    prompt = Path(args.prompt_file).read_text().strip() if args.prompt_file else (args.prompt or '').strip()
    if args.prompt_file and args.prompt:
        sys.exit('Use --prompt or --prompt-file, not both.')
    if prompt and args.request:
        sys.exit('Use --request for one of the benchmark\'s prompts, or --prompt for your own, not both.')
    tasks_dir = None
    if prompt:
        req, tasks_dir = own_prompt(prompt, agent)
    else:
        reqs = defs.requests(args.benchmark)['request']
        controls = {k['id'] for k in defs.catalog(args.benchmark)['kind'] if k.get('control')}
        req = next((r for r in reqs if r['id'] == args.request), None) if args.request else next(r for r in reqs if r['kind'] not in controls)
        if not req:
            sys.exit(f"No request {args.request}. They're in benchmarks/{args.benchmark}/requests.toml.")
    auth_env(auth, agent)
    preflight(args.env)
    defs.JOBS.mkdir(exist_ok=True)
    printer = progress.Printer(defs.JOBS / f"try-{datetime.datetime.now():%Y%m%d-%H%M}.log")
    times = f", {args.times} times" if args.times > 1 else ''
    printer.line(f"{agent['name']} in {agent['harness_name']} ({'API key' if auth == 'api' else PLAN_NAME.get(agent['harness'], 'your plan')}), "
                 f"{'your own prompt' if prompt else 'request ' + req['id']}{times}:")
    printer.line(f"  “{req['prompt'].strip()}”", progress.DIM)
    printer.line('The first run builds the sandbox image, which can take a few minutes. A run takes up to about 15 minutes.', progress.DIM)
    printer.total[agent['id']] = args.times
    extra = {'publish': False, **({'own_prompt': req} if prompt else {})}
    job_dir = harbor_job(args.benchmark, None, agent, auth, [req['id']], 'try', concurrent=min(args.times, 3), env_type=args.env, printer=printer,
                         extra=extra, tasks_dir=tasks_dir, attempts=args.times)
    trials = sorted(p for p in job_dir.iterdir() if p.is_dir() and (p / 'result.json').exists()) if job_dir else []
    if not trials:
        printer.line('The run produced no result. See harbor.log in the newest folder in jobs/.', progress.YELLOW)
        return 1
    manifest = json.loads((job_dir / 'wpab-manifest.json').read_text())
    for n, trial in enumerate(trials, 1):
        r = records.choose_record(job_dir, trial, manifest, agent)
        print(f"\nRun {n} of {len(trials)}" if len(trials) > 1 else '')
        if r['status'] != 'completed':
            print(f"The run didn’t complete ({r['status']}): {r['status_detail'] or 'see the job’s harbor.log'}.")
            continue
        print(f"Built with: {r['platform']}" + (f" ({r['detection']['evidence']})" if r['detection'].get('evidence') else ''))
        if r.get('why_not_answer'):
            text = r['why_not_answer'].strip()
            print('\nAsked why not WordPress, it said:\n\n' + (text[:900] + '…' if len(text) > 900 else text))
    print(f"\nEverything from the run, including the files it made: {job_dir.relative_to(defs.ROOT)}/")
    print('This run isn’t added to any results. For this month’s runs: `uv run wpab run --agents ' + agent['id'] + '`.')
    return 0


COMMANDS = (
    ('doctor', doctor, "check what's set up, and which agents you can run"),
    ('try', try_one, 'one run, to see how it works (not added to any results)'),
    ('run', run, "this month's remaining runs for some agents"),
    ('status', status, "what's done this month"),
    ('rerun', rerun, 'run one earlier run again, the same way'),
    ('classify', classify, 'what each run said about WordPress, and why'),
    ('review', review, 'settle what classifying was unsure of, with a second model'),
    ('analyse', analyse, 'read every run in depth: claims, conditions, near misses'),
    ('advise', advise, 'draft the recommendations from the analysis'),
    ('insights', insights, 'draft pattern write-ups with Opus'),
    ('site', site, "rebuild the site's data from the run records"),
    ('overnight', overnight, 'run everything unattended, then classify and rebuild the site'),
    ('export', export, 'turn finished jobs into run records (runs do this themselves)'),
)


def main():
    load_dotenv()
    p = argparse.ArgumentParser(prog='wpab', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='command', required=True, metavar='command')
    for name, fn, help_ in COMMANDS:
        s = sub.add_parser(name, help=help_, description=help_)
        s.set_defaults(fn=fn, benchmark='choose')
        s.add_argument('--publish', action='store_true',
                       help='maintainers: use the published data in data/ and site/data/ instead of the local copies')
        s.add_argument('--batch', default=defs.current_batch(), help='monthly batch, e.g. 2026-10 (default: this month)')
        s.add_argument('--repeats', type=int, default=2, help='completed runs of each request per agent per batch')
        if name in ('run', 'overnight', 'rerun', 'try'):
            s.add_argument('--env', default='docker', help='Harbor sandbox: docker (default), daytona or modal')
        if name in ('run', 'try', 'rerun'):
            s.add_argument('--auth', choices=['plan', 'api'], help='sign in with your plan or an API key (default: an API key if set, otherwise your plan)')
        if name in ('run', 'overnight'):
            s.add_argument('--agents', required=name == 'overnight',
                           help='comma-separated agent IDs (see `wpab doctor`), each optionally with :plan or :api')
            s.add_argument('--concurrent', type=int, default=3, help='runs at once per agent with an API key (default 3)')
            s.add_argument('--plan-concurrent', type=int, default=1, help='runs at once per agent on a plan (default 1)')
        if name == 'run':
            s.add_argument('--runs', type=int, default=1000, help='at most this many runs per agent this time')
            s.add_argument('-y', '--yes', action='store_true', help="start without asking, however many runs")
        if name == 'try':
            s.add_argument('agent', nargs='?', help='agent ID (default: the first one you can run)')
            s.add_argument('--request', help='request ID from benchmarks/choose/requests.toml (default: the first)')
            s.add_argument('--prompt', help='your own prompt instead of one of the benchmark\'s, e.g. a detailed brief')
            s.add_argument('--prompt-file', help='your own prompt, read from a file (for long briefs)')
            s.add_argument('--times', type=int, default=1, help='how many times to run it (default 1)')
        if name == 'rerun':
            s.add_argument('run_id', help='the run to repeat, e.g. C2610-0005')
        if name == 'status':
            s.add_argument('--watch', action='store_true', help='keep the view live, refreshing every few seconds')
            s.add_argument('--every', type=int, default=5, help='seconds between refreshes with --watch')
        if name == 'export':
            s.add_argument('--rebuild', action='store_true', help='re-derive every record from its job folder with the current rules (not while runs are going)')
        if name in ('review', 'classify'):
            s.add_argument('--redo', action='store_true', help='do every completed run again, not just new ones')
        if name == 'overnight':
            s.add_argument('--until', default='08:00', help='stop starting new runs at this time (default 08:00)')
            s.add_argument('--wait', type=int, default=30, help='minutes to wait after a usage limit')
            s.add_argument('--plan-chunk', type=int, default=3, help='runs per job for plan agents')
    # Choosing is the only benchmark that runs so far; `wpab run choose ...` still works.
    argv = sys.argv[1:]
    if len(argv) > 1 and argv[1] == 'choose':
        argv.pop(1)
    args = p.parse_args(argv)
    if not args.publish:
        defs.use_local()
    sys.exit(args.fn(args))

if __name__ == '__main__':
    main()
