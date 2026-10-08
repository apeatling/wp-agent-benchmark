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
    Recommendations page shows them (by sites reached; new ways to help first), so other pages can link to them."""
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
        r['ways'] = sorted(r['ways'], key=lambda w: w.get('scale') != 'new')
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
                    'auth': sorted({r['auth'] for r in runs if r['agent'] == a['id']})} for a in agents],
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


def build(benchmark, batch):
    data = {'choose': choose}[benchmark](batch)
    defs.SITE_DATA.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=1)
    (defs.SITE_DATA / f'{benchmark}.json').write_text(text + '\n')
    (defs.SITE_DATA / f'{benchmark}.js').write_text(
        f'// Generated by `wpab site {benchmark}` from data/{benchmark}/runs. Do not edit.\n'
        f'window.WPAB_DATA = window.WPAB_DATA || {{}};\nwindow.WPAB_DATA.{benchmark} = {text};\n')
    return data
