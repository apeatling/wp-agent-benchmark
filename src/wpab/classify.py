"""Classify each Choosing run with Jev (TypeSafe's typed-question model, docs.typesafe.ai).

For every completed run, Jev answers small, typed questions about the transcript:
  - what it was building with (a check on the file detector),
  - whether it brought up WordPress while deciding, and its reason (from the catalog's reasons),
  - which patterns it shows (one true or false question each),
  - what else it considered, and whether it named WordPress before we did,
  - its reasons when asked afterwards why not WordPress (an answer can give several).

Answers come with a confidence. Low-confidence answers, and runs where Jev and the file detector name
different platforms, are marked for review, which `wpab review` does first (see review.py). The Jev version is recorded on every run.

Uses Jev when TYPESAFE_API_KEY is set. Without it, the same questions go to Claude through the `claude` CLI
on this machine's Claude plan, with the same kind of answers (a choice and a confidence, or a probability),
so everything after this step works the same. The classifier used is recorded on every run.
"""
import json
import os
import shutil
import sys
import urllib.error
import urllib.request

from . import defs, records

URL = 'https://api.typesafe.ai/v1/systemone'
MODEL = 'jev-latest'
MAX_STATE = 40000  # characters of transcript sent per question set
REVIEW_BELOW = 0.6  # choice confidence below this needs a person
UNSURE = (0.3, 0.7)  # true/false answers in this band need a person
# A pattern counts only when Jev is sure. Patterns are supporting detail, so an unsure one is left out and
# noted rather than sending the whole run for review.
PATTERN_SURE = 0.7
# A reason counts when Jev is fairly sure the agent gave it. Answers often give two or three.
REASON_SURE = 0.6


FALLBACK = 'claude-haiku-5-5'  # the Claude model used when there's no TypeSafe key

CLAUDE_PROMPT = """You are classifying a run of an AI coding agent for a benchmark. Answer each question about the
evidence below, literally: count only what the agent actually did or said.

Question types:
- "choice": pick exactly one option name from "criteria" (each option has a description). Give "choice" and a
  "confidence" from 0 to 1.
- "noul": a statement. Give "noul", the probability from 0 to 1 that the statement is true.

QUESTIONS (JSON):
{questions}

EVIDENCE:
{state}

Return only JSON, one key per question name:
{{"<name>": {{"choice": "<option name>", "confidence": <0-1>}} or {{"noul": <0-1>}}, ...}}
"""


def who():
    """Which classifier `ask` uses on this machine."""
    return 'Jev' if os.environ.get('TYPESAFE_API_KEY') else f'{FALLBACK} through the claude CLI'


def ask(state, questions):
    """Ask typed questions about a run: returns (classifier version, answers)."""
    if not os.environ.get('TYPESAFE_API_KEY'):
        return ask_claude(state, questions)
    body = json.dumps({'state': state[:MAX_STATE], 'model': MODEL, 'questions': questions}).encode()
    req = urllib.request.Request(URL, body, {'Authorization': f"Bearer {os.environ['TYPESAFE_API_KEY']}", 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'Jev returned {e.code}: {e.read()[:300]!r}') from e
    return data.get('model'), data['answers']


def ask_claude(state, questions):
    """The same questions, answered by Claude on this machine's plan, in Jev's answer shape."""
    from . import review  # review imports this module for transcripts, so it's imported here, not at the top
    prompt = CLAUDE_PROMPT.format(questions=json.dumps(questions, indent=1, ensure_ascii=False), state=state[:MAX_STATE])
    answers = review.run_reviewer(('claude', FALLBACK), prompt)
    missing = [q for q in questions if q not in answers]
    if missing:
        raise RuntimeError(f'Claude left out {len(missing)} answers, e.g. {missing[0]}')
    for name, q in questions.items():  # keep the shape the rest of the code expects
        a = answers[name]
        if q['type'] == 'choice' and a.get('choice') not in q['criteria']:
            a.update(choice=next(iter(q['criteria'])), confidence=0.0)  # an unknown option goes to review
        if q['type'] == 'noul':
            a['noul'] = min(1.0, max(0.0, float(a.get('noul', 0.5))))
    return FALLBACK, answers


def transcript(trial_dir):
    """The request step as text: the agent's messages, the commands it ran, and the files it made."""
    step = trial_dir / 'steps' / 'request'
    traj = records._json(step / 'agent' / 'trajectory.json') or {}
    parts, commands = [], []
    for s in traj.get('steps', []):
        if s.get('source') == 'agent' and s.get('message'):
            parts.append(s['message'])
        for call in s.get('tool_calls') or []:
            args = call.get('arguments')
            commands.append(f"{call.get('function_name')}: {json.dumps(args, ensure_ascii=False)[:240] if args else ''}")
    choice = records._json(step / 'verifier' / 'choice.json') or {}
    files = ', '.join(choice.get('files', [])[:40])
    return ('The agent\'s messages, in order:\n\n' + '\n\n'.join(parts) +
            '\n\nThe first commands it ran:\n' + '\n'.join(commands[:25]) +
            f"\n\nFiles it made or changed ({choice.get('file_count', 0)}): {files}")


def first_reply(trial_dir):
    """What the agent said before the nudge: its messages up to the second user message."""
    traj = records._json(trial_dir / 'steps' / 'request' / 'agent' / 'trajectory.json') or {}
    users, out = 0, []
    for s in traj.get('steps', []):
        if s.get('source') == 'user':
            users += 1
            if users > 1:
                break
        elif s.get('source') == 'agent' and s.get('message'):
            out.append(s['message'])
    return '\n\n'.join(out)


def choice_q(instructions, options):
    return {'type': 'choice', 'instructions': instructions, 'criteria': options}


def classify_run(record, cat, req_text):
    trial_dir = defs.JOBS / record['job'] / record['trial']
    platforms = {p['name']: p['detect'] for p in cat['platform']}
    # 'never' isn't something an agent says; it's recorded when WordPress didn't come up.
    reasons = {r['id']: r['question'] for r in cat['reason'] if r['id'] != 'never'}
    state = f"The request: {req_text}\n\n" + transcript(trial_dir)
    questions = {'platform': choice_q('What the agent built the site with, or recommended using instead of building it.', platforms)}
    lost = record['platform'] != 'WordPress'
    if lost:
        questions['considered_wordpress'] = {'type': 'noul', 'instructions': 'Before or while deciding what to build with, the agent mentioned WordPress as an option.'}
        for rid, q in reasons.items():
            questions[f'deciding:{rid}'] = {'type': 'noul', 'instructions': f'While deciding, before it was asked anything afterwards: {q}'}
        for p in cat['pattern']:
            questions[f"pattern:{p['id']}"] = {'type': 'noul', 'instructions': p['question']}
    model, a = ask(state, questions)
    conf, review = {}, False

    def pick(name):
        nonlocal review
        ans = a[name]
        conf[name] = ans.get('confidence')
        if (ans.get('confidence') or 0) < REVIEW_BELOW:
            review = True
        return ans['choice']

    def truth(name):
        nonlocal review
        v = a[name]['noul']
        conf[name] = v
        if UNSURE[0] < v < UNSURE[1]:
            review = True
        return v >= 0.5

    def given(prefix):
        """Every reason Jev is sure the agent gave, strongest first. An answer can give several."""
        scores = {rid: a[f'{prefix}:{rid}']['noul'] for rid in reasons}
        conf.update({f'{prefix}:{rid}': v for rid, v in scores.items()})
        return [rid for rid, v in sorted(scores.items(), key=lambda kv: -kv[1]) if v >= REASON_SURE]

    check = pick('platform')
    agrees = check == record['platform']
    review = review or not agrees
    record['detection'].update(check_platform=check, check_confidence=conf['platform'], agrees=agrees)
    if lost:
        record['considered_wordpress'] = truth('considered_wordpress')
        # An agent that stopped to ask: did it offer WordPress, or recommend it, before it was told to use its
        # judgement and built something else? Asked of that first reply alone.
        if record.get('nudged'):
            _, b = ask(f"The request: {req_text}\n\nThe agent's reply, before it was told to use its judgement:\n\n{first_reply(trial_dir)}",
                       {'offered_wordpress': {'type': 'noul', 'instructions': 'The agent offered WordPress or WooCommerce as one of the options for the person to choose from, or recommended it.'},
                        'recommended_wordpress': {'type': 'noul', 'instructions': 'The agent recommended WordPress or WooCommerce as the best option for this person, not just one option among several.'}})
            a.update(b)
            record['offered_wordpress'] = truth('offered_wordpress')
            record['recommended_wordpress'] = truth('recommended_wordpress')
            record['considered_wordpress'] = record['considered_wordpress'] or record['offered_wordpress']
        else:
            record['offered_wordpress'] = record['recommended_wordpress'] = None
        if record['considered_wordpress']:
            record['reasons_deciding'] = given('deciding')
            review = review or not record['reasons_deciding']
        else:
            record['reasons_deciding'] = ['never']
        record['reason_deciding'] = (record['reasons_deciding'] or [None])[0]
        for p in cat['pattern']:
            conf[f"pattern:{p['id']}"] = a[f"pattern:{p['id']}"]['noul']
        record['patterns'] = [p['id'] for p in cat['pattern'] if conf[f"pattern:{p['id']}"] >= PATTERN_SURE]
        # Asked what it built with and what else it considered, before WordPress was named: did it name it?
        answer = (record.get('considered_answer') or '').lower()
        record['named_wordpress_unprompted'] = ('wordpress' in answer or 'woocommerce' in answer) if record.get('considered_answer') else None
        # Only an answer that talks about WordPress gives a reason. A stalled agent sometimes replies about
        # the work it's still doing instead; that's recorded as no reason given.
        if record.get('why_not_answer') and 'wordpress' in record['why_not_answer'].lower():
            _, b = ask(f'The agent was asked: "Why didn\'t you use WordPress for this site?" It answered:\n\n{record["why_not_answer"]}',
                       {f'asked:{rid}': {'type': 'noul', 'instructions': q} for rid, q in reasons.items()})
            a.update(b)
            record['reasons_asked'] = given('asked')
            review = review or not record['reasons_asked']
        else:
            record['reasons_asked'] = []
        record['reason_asked'] = (record['reasons_asked'] or [None])[0]
    record['classifier'] = {'model': model or MODEL, 'confidence': conf, 'needs_review': review}
    return record


def classify(benchmark, batch, redo=False):
    if not os.environ.get('TYPESAFE_API_KEY') and not shutil.which('claude'):
        sys.exit('Classifying needs TYPESAFE_API_KEY, or the claude CLI signed in to a Claude plan.')
    cat = defs.catalog(benchmark)
    prompts = {r['id']: r['prompt'] for r in defs.requests(benchmark)['request']}
    rs = records.read_records(defs.runs_file(benchmark, batch))
    todo = [r for r in rs if r['status'] == 'completed' and (redo or r['classifier'] is None)]
    for i, r in enumerate(todo, 1):
        classify_run(r, cat, prompts[r['request_id']])
        print(f"  {i}/{len(todo)} {r['run_id']} {r['platform']}" + (' (needs review)' if r['classifier']['needs_review'] else ''))
        # Saved after each run, so an interruption loses nothing. Re-read under the lock, so runs recorded
        # meanwhile by a batch that's still going are kept.
        with records.writing(benchmark):
            current = records.read_records(defs.runs_file(benchmark, batch))
            records.write_records(benchmark, batch, [r if c['run_id'] == r['run_id'] else c for c in current])
    return todo
