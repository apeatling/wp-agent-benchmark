"""Readable progress for long runs: one line per finished run, with a running count per agent.

Harbor's own detailed output goes to a log file next to the job; the terminal shows only this. Every line
is also written to the session log, so an overnight run can be followed with `tail -f`.
"""
import datetime
import json
import sys
import threading
import time

from . import defs, records

GREEN, BLUE, DIM, YELLOW, RED, RESET = '\033[32m', '\033[34m', '\033[2m', '\033[33m', '\033[31m', '\033[0m'


class Printer:
    def __init__(self, log_path=None):
        self.lock = threading.Lock()
        self.log = log_path.open('a', buffering=1) if log_path else None
        self.color = sys.stdout.isatty()
        self.done = {}   # agent id -> completed this session
        self.total = {}  # agent id -> runs to do this session

    def line(self, text, color=''):
        stamp = f'{datetime.datetime.now():%H:%M}'
        with self.lock:
            print(f'{DIM}{stamp}{RESET}  {color}{text}{RESET}' if self.color else f'{stamp}  {text}', flush=True)
            if self.log:
                self.log.write(f'{stamp}  {text}\n')

    def run(self, agent, request, outcome, seconds, counted):
        """One finished run."""
        if counted:
            self.done[agent['id']] = self.done.get(agent['id'], 0) + 1
        mins, secs = divmod(int(seconds or 0), 60)
        count = f"{self.done.get(agent['id'], 0)}/{self.total.get(agent['id'], '?')}"
        color = BLUE if outcome == 'WordPress' else (YELLOW if not counted else '')
        self.line(f"{agent['name']:<16} {request:<12} {outcome:<26} {mins}m {secs:02d}s  {count}", color)

    def started(self, agent, request):
        """A run has begun, so there's something on screen during long runs."""
        self.line(f"{agent['name']:<16} {request:<12} started", DIM)


def outcome_of(trial_dir):
    """A short description of how a finished trial went, and whether it will count."""
    result = json.loads((trial_dir / 'result.json').read_text())
    choice = trial_dir / 'steps' / 'request' / 'verifier' / 'choice.json'
    exc = result.get('exception_info') or {}
    if exc and records.LIMIT.search(json.dumps(exc)):
        return 'usage limit (not counted)', False
    if exc:
        return f"error: {exc.get('exception_type', 'unknown')} (not counted)", False
    if choice.exists():
        return json.loads(choice.read_text())['platform'], True
    return 'no result (not counted)', False


def seconds_of(trial_dir):
    r = json.loads((trial_dir / 'result.json').read_text())
    try:
        parse = lambda s: datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
        return (parse(r['finished_at']) - parse(r['started_at'])).total_seconds()
    except (KeyError, TypeError, ValueError):
        return 0


def watch(job, agent, printer, stop):
    """Print each trial in a job as it finishes, until `stop` is set."""
    seen, begun = set(), set()
    job_dir = defs.JOBS / job
    while True:
        finished = stop.is_set()
        if job_dir.exists():
            for t in sorted(job_dir.iterdir()):
                if t.is_dir() and t.name not in begun:
                    begun.add(t.name)
                    printer.started(agent, t.name.split('__')[0])
                if t.name in seen or not (t / 'result.json').exists():
                    continue
                try:
                    if not json.loads((t / 'result.json').read_text()).get('finished_at'):
                        continue
                    outcome, counted = outcome_of(t)
                except (OSError, ValueError):
                    continue
                seen.add(t.name)
                printer.run(agent, t.name.split('__')[0], outcome, seconds_of(t), counted)
        if finished:
            return
        time.sleep(3)
