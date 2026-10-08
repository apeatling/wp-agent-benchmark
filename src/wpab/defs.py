"""The benchmark definitions in benchmarks/, and where data lives. See docs/data.md."""
import datetime
import subprocess
import tomllib
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOBS = ROOT / 'jobs'
DATA = ROOT / 'data'
# Where runs, analysis and site data are written. Published by default for code that reads them; the wpab
# command switches to the local copies unless it's given --publish (see use_local).
OUT = DATA
SITE_DATA = ROOT / 'site' / 'data'
LOCAL_OUT = DATA / 'local'
LOCAL_SITE_DATA = ROOT / 'site' / 'data-local'


def use_local():
    """Write runs, analysis and site data to gitignored local folders, so trying the benchmark never touches
    the published results."""
    global OUT, SITE_DATA
    OUT, SITE_DATA = LOCAL_OUT, LOCAL_SITE_DATA


def local():
    return OUT == LOCAL_OUT
SCHEMA = ROOT / 'schema'


@cache
def agents():
    """Agents by ID, in the order they're listed."""
    return {a['id']: a for a in tomllib.loads((ROOT / 'benchmarks' / 'agents.toml').read_text())['agent']}


@cache
def environments():
    """Sandbox profiles by ID."""
    return {e['id']: e for e in tomllib.loads((ROOT / 'benchmarks' / 'environments.toml').read_text())['environment']}


@cache
def catalog(benchmark):
    return tomllib.loads((ROOT / 'benchmarks' / benchmark / 'catalog.toml').read_text())


@cache
def requests(benchmark):
    return tomllib.loads((ROOT / 'benchmarks' / benchmark / 'requests.toml').read_text())


def current_batch():
    """This month's batch, e.g. 2026-10."""
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m')


def runs_file(benchmark, batch):
    return OUT / benchmark / 'runs' / f'{batch}.jsonl'


def git_commit():
    """The runner's commit, marked -dirty if there are uncommitted changes."""
    try:
        out = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True)
        dirty = subprocess.run(['git', 'status', '--porcelain', '--', 'src', 'benchmarks', 'tasks'], cwd=ROOT, capture_output=True, text=True).stdout
        return out.stdout.strip() + ('-dirty' if dirty.strip() else '')
    except (OSError, subprocess.CalledProcessError):
        return None
