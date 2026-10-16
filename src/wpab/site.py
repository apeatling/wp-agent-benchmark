"""Build the site's data from the definitions and the run records: site/data/<benchmark>.json.

The JSON is the site's whole input: who was tested, what was asked, every counted run (compactly), and
the headline for each batch so far. The same JSON is wrapped as site/data/<benchmark>.js so the static
pages can load it with a script tag. Never edit either by hand; run `wpab site` again.

Only completed runs are included; the run records keep the rest.
"""
import collections
import datetime
import json
import re

from . import defs, records

SCHEMA_VERSION = '1.0'


def batch_info(batch):
    month = datetime.date(int(batch[:4]), int(batch[5:7]), 1)
    return {'id': batch, 'name': month.strftime('%B %Y'), 'short': month.strftime('%B')}


def logo_key(agent):
    """The maker logo the site draws for an agent: the first word of its model name."""
    return re.sub(r'[^a-z].*', '', agent['name'].lower())


def advice(batch):
    from . import deep
    base = defs.OUT / 'choose' / 'analysis' / batch
    if not (base / 'advice.md').exists():
        return None
    adv = {**deep.sections(batch), 'reviewed': (base / 'advice.reviewed').exists()}
    assign_ids(adv)
    adv['by_reason'] = reason_links(batch, adv)
    from .deep import dashboard_reasons
    missing = [r['name'] for r in dashboard_reasons(batch) if r['id'] not in adv['by_reason']]
    if missing:
        print(f"  Note: no recommendation answers {', '.join(missing)}; the Data page says 'No recommendation yet'.")
    for s in adv['sections']:
        if s.get('reach'):
            s['reach'].pop('runs', None)   # only needed in the build, not on the page
    return adv


def assign_ids(adv):
    """Give every recommendation, way to help and closing section the id its permalink uses, in the order the
    Recommendations page shows them (problems by sites reached; ideas by impact), so other pages can link to them."""
    slug = lambda t: re.sub(r'^-|-$', '', re.sub(r'[^a-z0-9]+', '-', re.sub(r'^\d+\.\s*', '', re.sub(r'<[^>]+>', '', t)).lower())) or 'idea'
    used = set()

    def uid(text):
        base, n, i = slug(text), slug(text), 2
        while n in used:
            n, i = f'{base}-{i}', i + 1
        used.add(n)
        return n
    recs = sorted((x for x in adv['sections'] if x.get('recommendation')), key=lambda x: -x['reach']['sites'])
    for r in recs:
        r['id'] = uid(r['title'])
        for w in r['ways']:
            w['id'] = uid(w['html'])
    for x in adv['sections']:
        if not x.get('recommendation'):
            x['id'] = uid(x['title'])


def reason_links(batch, adv):
    """For each reason on the Data page, every recommendation that says it answers it (the "reasons" the advice
    tags each recommendation with), most sites reached first, each with the ways to help that address the reason:
    the ones tagged with it, or the first ones listed when ways aren't tagged. Keeps the two pages in step."""
    out = {}
    for r in sorted((x for x in adv['sections'] if x.get('recommendation')), key=lambda x: -x['reach']['sites']):
        for rid in r.get('answers', {}).get('reasons', []):
            tagged = [w for w in r['ways'] if rid in (w.get('reasons') or [])]
            ways = tagged or ([] if any(w.get('reasons') for w in r['ways']) else r['ways'])
            out.setdefault(rid, []).append({
                'id': r['id'], 'title': re.sub(r'^\d+\.\s*', '', r['title']),
                'ways': [{'id': w['id'], 'text': re.sub(r'<[^>]+>', '', w['html'])} for w in ways[:2]],
                'more': max(0, len(ways) - 2)})
    return out


def choose(batch):
    cat, reqs = defs.catalog('choose'), defs.requests('choose')
    batches = sorted(p.stem for p in (defs.OUT / 'choose' / 'runs').glob('*.jsonl') if p.stem <= batch)
    every = {b: [r for r in records.read_records(defs.runs_file('choose', b)) if r['status'] == 'completed'] for b in batches}
    runs = every[batch]
    used = {r['agent'] for r in runs}
    agents = [a for a in defs.agents().values() if a['id'] in used]

    checked = [r for r in runs if (r.get('detection') or {}).get('agrees') is not None]
    insights_file = defs.OUT / 'choose' / 'insights' / f'{batch}.json'
    reviewed = json.loads(insights_file.read_text()) if insights_file.exists() else {}
    insights = reviewed.get('patterns', {})
    # A quote for each reason, picked in the insights draft and checked by a person.
    quotes = {k: {'text': v['quote'], 'run': v['quote_run']} for k, v in reviewed.get('reasons', {}).items()}
    insights = {k: {f: v[f] for f in ('title', 'saw', 'quote', 'ideas') if v.get(f)} for k, v in insights.items() if v.get('supported', True)}

    def headline(rs):
        """Share of sites WordPress suits, built with WordPress, by the head agents tested that batch."""
        built = [r for r in rs if not r['control'] and r['built'] and defs.agents()[r['agent']]['head']]
        return {'n': len(built), 'wordpress': sum(r['platform'] == 'WordPress' for r in built)}

    return {
        'schema_version': SCHEMA_VERSION,
        'generated': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'batch': batch_info(batch),
        'suite_version': reqs['version'],
        'agents': [{'id': a['id'], 'name': a['name'], 'harness': a['harness_name'], 'logo': logo_key(a), 'head': a['head'],
                    'auth': sorted({r['auth'] for r in runs if r['agent'] == a['id']}), 'environment': a.get('environment')} for a in agents],
        # The sandboxes agents work in: the maker's documented environment, or a typical developer machine.
        'environments': [{k: e.get(k) for k in ('id', 'name', 'description', 'docker', 'sources')} for e in defs.environments().values()],
        'kinds': cat['kind'],
        'requests': [{'id': r['id'], 'kind': r['kind'], 'prompt': r['prompt'], **({'fixture': r['fixture']} if r.get('fixture') else {})} for r in reqs['request']],
        'groups': cat['group'],
        'platforms': cat['platform'],
        'reasons': [{k: r.get(k) for k in ('id', 'name', 'owner', 'lever', 'pattern')} | {'quote': quotes.get(r['id'])} for r in cat['reason']],
        # Each pattern's write-up (what we saw, ideas to try) comes from the reviewed insights for the batch, if any.
        'patterns': [{k: p[k] for k in ('id', 'short', 'question')} | insights.get(p['id'], {}) for p in cat['pattern']],
        # The month's advice, as written (data/choose/analysis/<batch>/advice.md), split for the page without
        # changing a word. Shown as a draft until a person marks it reviewed (advice.reviewed next to it).
        'advice': advice(batch),
        # Earlier months' advice, so past recommendations stay readable.
        'advice_history': {b: advice(b) for b in batches if b != batch and advice(b)},
        'detect_check': {'runs': len(checked), 'agree': sum(r['detection']['agrees'] for r in checked)},
        'runs': [{
            'id': r['run_id'], 'agent': r['agent'], 'request': r['request_id'], 'kind': r['kind'], 'control': r['control'],
            'platform': r['platform'], 'group': r['platform_group'], 'built': r['built'], 'nudged': r['nudged'],
            'considered': r['considered_wordpress'], 'offered': r.get('offered_wordpress'), 'recommended': r.get('recommended_wordpress'),
            'unprompted': r.get('named_wordpress_unprompted'), 'reason': r['reason_deciding'], 'reason_asked': r['reason_asked'],
            'reasons': r.get('reasons_deciding') or [], 'reasons_asked': r.get('reasons_asked') or [], 'considered_answer': r.get('considered_answer'),
            'patterns': r['patterns'], 'started': r.get('started_at'), 'minutes': round((r['duration_s'] or 0) / 60), 'answer': r['why_not_answer'],
            'evidence': (r.get('detection') or {}).get('evidence'), 'review': bool((r.get('classifier') or {}).get('needs_review')),
            'reviewed_by': (((r.get('classifier') or {}).get('review') or {}).get('model')),
            'review_notes': (((r.get('classifier') or {}).get('review') or {}).get('notes')),
        } for r in runs],
        'history': [{'batch': b, **headline(rs)} for b, rs in every.items()],
    }


def started(r):
    """When a run's job started, from its name (try-build-<agent>-YYYYMMDD-HHMMSS, in UTC)."""
    m = re.search(r'(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})', r['job'])
    return f'{m[1]}-{m[2]}-{m[3]}T{m[4]}:{m[5]}:{m[6]}Z' if m else None


def owner_said(r):
    """What the scripted owner said in a run, turn by turn: its fixed lines and the request's own facts, never the
    agent's words (run transcripts are never published)."""
    f = defs.JOBS / r['job'] / r['trial'] / 'owner-dialogue.json'
    if not f.exists():
        return []
    return [t.get('reply') for t in json.loads(f.read_text()).get('turns', []) if t.get('reply')]


# The site's names for the ways in: "WordPress's MCP adapter plugin" (the official MCP Adapter plugin), "the MCP
# adapter" for short. The deeper read wrote "MCP connector"; third-party plugins are never named. Quotes (the
# agent's or the owner's words) are left as said.
_TERMS = [
    (re.compile(r"(\b[Tt]he )?\bAI Engine(?: MCP)?(?: connect(?:or|ion))?\b"), lambda m: (m[1] or '') + 'third-party MCP plugin'),
    (re.compile(r"(\b[Tt]he )?\bthird-party (?:MCP )?connector(s?)\b", re.I), lambda m: (m[1] or '') + 'third-party MCP plugin' + m[2]),
    (re.compile(r"(\b[Tt]he )?((?:official |WordPress(?:'s|’s)? (?:own )?)+)?(?:MCP )?\bconnector(s?)\b", re.I),
     lambda m: (m[1] or ('the ' if m[2] else '')) + 'MCP adapter' + m[3]),
]
# The agents were never told to use the REST API, so the setup without the MCP adapter is "no MCP adapter installed".
# Only the advice framed it as the REST API; elsewhere "REST API" is what an agent actually called.
_SETUP_TERMS = [
    (re.compile(r"\bover (?:the )?REST(?: API)?\b", re.I), lambda m: 'with no MCP adapter installed'),
    (re.compile(r"\bREST API runs\b"), lambda m: 'runs with no MCP adapter installed'),
    (re.compile(r"\b(both|neither) routes?\b"), lambda m: m[1] + (' setups' if m[1] == 'both' else ' setup')),
    # A request's outcome is "completed", not "done".
    (re.compile(r"\bDone in full\b"), lambda m: 'Completed'),
]
# The test texts are "prompts", as on Choosing. An HTTP request, a request form, or an agent's own request (to the
# owner, or "a request to ...") stays a request.
_TERMS.append((re.compile(r"(?<!HTTP )(?<!POST )(?<!GET )(?<!API )(?<!REST )(?<!pull )(?<!site )(?<!access )(?<!its )\b([Rr])equest(s?)\b(?! form| to\b)"),
               lambda m: ('P' if m[1] == 'R' else 'p') + 'rompt' + m[2]))
_QUOTED = re.compile(r'("[^"]*"|“[^”]*”|`[^`]*`)')


def public_terms(x, key=None, setup=False):
    setup = setup or key == 'advice'
    if isinstance(x, dict):
        return {k: v if k in ('quote', 'owner_said', 'prompt', 'setups', 'id') else public_terms(v, k, setup) for k, v in x.items()}
    if isinstance(x, list):
        return [public_terms(v, key, setup) for v in x]
    if not isinstance(x, str):
        return x
    parts = _QUOTED.split(x)
    for i in range(0, len(parts), 2):
        for pattern, repl in _TERMS + (_SETUP_TERMS if setup else []):
            parts[i] = pattern.sub(repl, parts[i])
    out = ''.join(parts)
    # A sentence that now starts with the new name starts with a capital.
    return re.sub(r'(^|[.!?]\s+)(the|third-party|MCP|with)\b', lambda m: m[1] + m[2][0].upper() + m[2][1:], out) if out != x else out


def building(batch):
    """Building's site data for a batch: the requests and how the agent reached the site, every run with what was
    checked and what stopped it, the dead ends (the catalogue, with the deeper read's write-ups), and what the
    agents themselves missed. From data/local/build-runs.jsonl (wpab.build_runs) and
    data/local/build-analysis/<batch>/ (wpab.build_analysis)."""
    import tomllib
    source = defs.ROOT / 'benchmarks' / 'build'
    reqs = tomllib.loads((source / 'requests.toml').read_text())
    setups = tomllib.loads((source / 'setups.toml').read_text())['setup']
    catalogue = tomllib.loads((source / 'dead_ends.toml').read_text())
    rows = [json.loads(l) for l in (defs.ROOT / 'data' / 'local' / 'build-runs.jsonl').read_text().splitlines() if l.strip()]
    # Runs whose agent never started (a login or usage limit) aren't results.
    runs = [r for r in rows if r.get('batch') == batch and not r.get('error')]
    if not runs:
        raise SystemExit(f'No Building runs for batch {batch} in data/local/build-runs.jsonl. Run `uv run python -m wpab.build_runs` first.')
    # Stable run IDs, like Choosing's (C2610-0005): B, the year and month the run started, and its number that month,
    # in start order across every batch, so an ID never changes when a later batch is added.
    stamp = lambda r: re.search(r'(\d{8}-\d{6})', r['job']).group(1)
    every = sorted((r for r in rows if not r.get('error') and re.search(r'\d{8}-\d{6}', r['job'])), key=lambda r: (stamp(r), r['trial']))
    run_id, count = {}, {}
    for r in every:
        month = stamp(r)[2:6]
        count[month] = count.get(month, 0) + 1
        run_id[r['trial']] = f'B{month}-{count[month]:04d}'
    analysis = defs.ROOT / 'data' / 'local' / 'build-analysis' / batch
    read = lambda name: json.loads((analysis / name).read_text()) if (analysis / name).exists() else None
    grouped, written = read('grouped.json') or {}, read('dead_ends.json') or []
    deep_read = {x['run_id']: x for x in (read('runs.json') or [])}
    # Agents wrote in markdown; quotes show their words plain, without the ** and backticks.
    plain = lambda t: re.sub(r'\*\*|`', '', t) if t else t
    quote = lambda r, k: next((plain(i['quote']) for i in deep_read.get(r['trial'], {}).get('not_done', []) if i['check'] == k and i.get('quote_found')), None)
    notes = lambda r, key: [{'what': i['what'], 'quote': plain(i['quote'])} for i in deep_read.get(r['trial'], {}).get(key, []) if i.get('quote_found')]
    used = {r['agent'] for r in runs}
    agents = [a for a in defs.agents().values() if a['id'] in used]
    # Check names, from the runs (each request's checks are its own).
    names = {}
    for r in runs:
        for k, c in r['checks'].items():
            names.setdefault(r['request'], {}).setdefault(k, c.get('name', k))
    guards = {'site_works', 'nothing_lost', 'no_new_access'}
    return public_terms({
        'schema_version': SCHEMA_VERSION,
        'generated': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'batch': {'id': batch, 'name': {'base-1': 'First batch', 'base-2': 'Second batch', 'base-3': 'October 2026'}.get(batch, batch) + f', {len(runs)} runs'},
        'suite_version': reqs['version'],
        'agents': [{'id': a['id'], 'name': a['name'], 'harness': a['harness_name'], 'logo': logo_key(a)} for a in agents],
        'needs': [{'id': k, 'name': v['name']} for k, v in reqs['need'].items()],
        'setups': [{k: s.get(k) for k in ('id', 'name', 'kind', 'plugins')} for s in setups],
        'requests': [{'id': r['id'], 'need': r['need'], 'fixture': r['fixture'], 'size': r['size'], 'prompt': r['prompt'].strip(),
                      'outside_api': r.get('outside_api', False), 'product': r.get('product'), 'follow_up': r.get('follow_up'),
                      'checks': [{'id': k, 'name': v, 'guard': k in guards} for k, v in names.get(r['id'], {}).items()]}
                     for r in reqs['request'] if r['id'] in {x['request'] for x in runs}],  # not held-out requests
        # The catalogue's dead ends, each with the deeper read's write-up where it has one.
        'dead_ends': [{k: d.get(k) for k in ('id', 'title', 'seen', 'what', 'setups', 'requests')}
                      | {'write_up': next(({k: w[k] for k in ('title', 'seen', 'what_happens', 'quote', 'quote_run', 'where')}
                                           for w in written if w['catalogue_id'] == d['id']), None)}
                      for d in catalogue['dead_end'] if not d.get('retired')],
        # What the deeper read found, grouped: on WordPress's side (finer than the catalogue), the agents' side,
        # and faults in the benchmark itself (fixed before the next batch).
        'found': {key: [{'title': g['title'], 'catalogue_id': g.get('catalogue_id'), 'runs': g['runs'], 'requests': g['requests'],
                         'examples': [{'run': m['run_id'], 'check': m['check'], 'what_stopped': m['what_stopped'], 'quote': plain(m.get('quote'))}
                                      for m in g['members'][:4]]}
                        for g in grouped.get(key, [])] for key in ('dead_ends', 'agent_side', 'benchmark_faults')},
        'write_ups': [w | {'quote': plain(w.get('quote'))} for w in written if w['catalogue_id'] == 'new'],
        # The recommendations, written from the dead ends and misses on WordPress's own routes (wpab.build_analysis advise).
        # Plus any ideas written by hand and reviewed (advice-additions.json), so a re-run of the advise step keeps them,
        # and each idea's pitch, the paragraphs that open its page, written by hand and reviewed (pitches.json).
        'advice': (lambda a, extra, pitch: a and {**a, 'ideas': [x | ({'pitch': pitch[x['id']]} if x['id'] in pitch else {}) for x in
                                                                 a['ideas'] + [x for x in extra if x['id'] not in {i['id'] for i in a['ideas']}]]})(
            read('advice.json'), read('advice-additions.json') or [], read('pitches.json') or {}),
        'routes': [{k: x.get(k) for k in ('id', 'title', 'escalation')} for x in catalogue['route']],
        'runs': [{'id': run_id[r['trial']], 'trial': r['trial'], 'started': started(r), 'agent': r['agent'], 'request': r['request'], 'need': r['need'], 'setup': r['setup'],
                  'kind': r['setup_kind'], 'success': r['success'], 'success_alone': r['success_alone'],
                  'success_within': r['success_within_access'], 'escalated': r['escalated'], 'routes': r['routes'],
                  'asked_owner': r['asked_owner'], 'told_owner': r.get('told_owner'), 'owner_said': owner_said(r), 'turns': r['turns'], 'end': r['end'], 'minutes': r['minutes'], 'connector_calls': r.get('connector_calls'),
                  'checks': {k: {f: c.get(f) for f in ('status', 'dead_ends', 'cause', 'what_stopped', 'detail', 'required') if c.get(f) is not None}
                             | {'passed': c['status'] in ('unaided', 'after_owner') and not c.get('escalated_run')}
                             | ({'quote': quote(r, k)} if quote(r, k) else {})
                             for k, c in r['checks'].items()},
                  'told_wrong': notes(r, 'told_wrong'), 'handled_well': notes(r, 'handled_well')}
                 for r in runs],
    })



def write_js(benchmark, data, name, out=None):
    text = json.dumps(data, ensure_ascii=False, indent=1)
    ((out or defs.SITE_DATA) / f'{name}.js').write_text(
        f'// Generated by `wpab site {benchmark}` from data/{benchmark}/runs. Do not edit.\n'
        f'window.WPAB_DATA = window.WPAB_DATA || {{}};\nwindow.WPAB_DATA.{benchmark} = {text};\n')
    return text


def public_build(data):
    """Building's data as published (site/data/build.js): runs with and without WordPress's MCP adapter only. Third-party
    MCP plugins are a reference figure in the hero, so their runs keep only what that figure needs (need and outcome),
    and nothing about them is named: no setup, run IDs, prompts' third-party runs, or dead ends seen only there."""
    third = {r['id'] for r in data['runs'] if r['kind'] == 'third'}
    ours = lambda q: not q.endswith('-ai-engine')
    def keep(groups):
        out = []
        for g in groups:
            g = g | {'requests': [q for q in g.get('requests') or [] if ours(q)]}
            if 'examples' in g:
                g['examples'] = [m for m in g['examples'] if m['run'] not in third and ours(m['run'].split('__')[0])]
            if g['requests']:
                out.append(g)
        return out
    return data | {
        'setups': [x for x in data['setups'] if x['kind'] != 'third'],
        'dead_ends': [d for d in data['dead_ends'] if d.get('setups') != ['third']],
        'found': {k: keep(v) for k, v in data['found'].items()},
        'write_ups': [w for w in keep(data['write_ups']) if w.get('quote_run') not in third and ours((w.get('quote_run') or '').split('__')[0])],
        'runs': [r for r in data['runs'] if r['kind'] != 'third'],
        'reference': [{k: r[k] for k in ('need', 'success', 'success_within', 'told_owner')} for r in data['runs'] if r['kind'] == 'third'],
    }


def build(benchmark, batch):
    make = {'choose': choose, 'build': building}[benchmark]
    data = make(batch)
    # Building's full data (third-party runs and all) only ever goes to the local-only folder; the public site
    # gets the scrubbed copy below, never this one.
    out = defs.LOCAL_SITE_DATA if benchmark == 'build' else defs.SITE_DATA
    out.mkdir(parents=True, exist_ok=True)
    text = write_js(benchmark, data, benchmark, out)
    (out / f'{benchmark}.json').write_text(text + '\n')
    if benchmark == 'build':  # what the public site reads, scrubbed (public_build), next to Choosing's
        pub = json.dumps(public_build(data), ensure_ascii=False, indent=1)
        (defs.ROOT / 'site' / 'data' / 'build.js').write_text(
            f'// Generated by `wpab site build` from the run records, without third-party runs. Do not edit.\n'
            f'window.WPAB_DATA = window.WPAB_DATA || {{}};\nwindow.WPAB_DATA.build = {pub};\n')
    # Earlier months keep their own data, written once when a later month is built, so links into an earlier
    # month's recommendations (run pages) still open its runs. The run page loads it by the run ID's month.
    for b in sorted(p.stem for p in (defs.OUT / benchmark / 'runs').glob('*.jsonl') if p.stem < batch):
        if not (out / f'{benchmark}-{b}.js').exists():
            write_js(benchmark, make(b), f'{benchmark}-{b}', out)
    return data
