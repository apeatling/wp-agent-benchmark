"""Match a Building run's evidence to the dead ends and routes in benchmarks/build/dead_ends.toml.

Evidence: the site's activity log (what the agent asked WordPress for, and its answers), the classifier's notes
on what the agent told the owner, and the checks. See dead_ends.toml for the rules.
"""
import json
import re
import tomllib
from functools import cache

from . import defs

YES = 0.6
CATALOGUE = defs.ROOT / 'benchmarks' / 'build' / 'dead_ends.toml'


@cache
def catalogue():
    return tomllib.loads(CATALOGUE.read_text())


def read_activity(path, connector_path=None):
    """The agent's requests from an activity log: not the checks', and not WordPress's own scheduled tasks.
    connector_path: the setup's connector endpoint, for logs from before the connector marked its requests."""
    if not path or not path.exists():
        return []
    out = []
    for line in path.read_text(errors='replace').splitlines():
        try:
            a = json.loads(line)
        except ValueError:
            continue
        if a.get('from') not in ('agent', 'visitor') or a.get('path', '').startswith('/wp-cron'):
            continue
        if connector_path and a.get('path', '').split('?')[0] == connector_path:
            a['kind'], a['via'] = 'connector', 'connector'
        out.append(a)
    return out


def _matches(entry, a):
    """Whether one activity entry matches one rule (every field given must match)."""
    values = a.get('values') or {}
    fields = {
        'kind': a.get('kind'), 'route': a.get('route'), 'method': a.get('method'), 'path': a.get('path'),
        'status': str(a.get('status', '')), 'via': a.get('via'), 'sent': ' '.join(str(x) for x in a.get('sent') or []),
        'mcp_method': (a.get('mcp') or {}).get('method'), 'action': values.get('action'),
        'tool': ' '.join(filter(None, [(a.get('mcp') or {}).get('tool'), (a.get('mcp') or {}).get('ability')])) or None,
        'roles': ' '.join(values.get('roles') or []) if isinstance(values.get('roles'), list) else values.get('roles'),
    }
    for k, pattern in entry.items():
        if k == 'kind':
            if fields['kind'] != pattern:
                return False
        elif not (fields.get(k) is not None and re.search(pattern, str(fields[k]))):
            return False
    return True


def found(rules, activity):
    return any(_matches(e, a) for e in rules for a in activity)


def routes(activity):
    """{route id: number of matching requests}, and whether any of them is an escalation."""
    out = {}
    for r in catalogue()['route']:
        n = sum(1 for a in activity if any(_matches(e, a) for e in r['activity']))
        if n:
            out[r['id']] = n
    escalated = any(r.get('escalation') for r in catalogue()['route'] if r['id'] in out)
    return out, escalated


def explain(check, setup_kind, activity, notes, request=None):
    """Dead-end IDs that explain a check not done within the access given, or ['unexplained']."""
    def hits(fallback):
        out = []
        for d in catalogue()['dead_end']:
            if bool(d.get('fallback')) != fallback or (d['check'] != '*' and check not in ([d['check']] if isinstance(d['check'], str) else d['check'])) or setup_kind not in d.get('setups', [setup_kind]):
                continue
            if d.get('retired') or (request and request not in d.get('requests', [request])):
                continue
            if any(notes.get(n, 0) >= YES for n in d.get('said', [])) or found(d.get('activity', []), activity):
                out.append(d['id'])
        return out
    return hits(False) or hits(True) or ['unexplained']


def title(dead_end_id):
    return next((d['title'] for d in catalogue()['dead_end'] if d['id'] == dead_end_id), dead_end_id)
