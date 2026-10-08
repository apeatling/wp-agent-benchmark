"""Build the Harbor tasks in tasks/ from the benchmark definitions in benchmarks/.

Each request in benchmarks/choose/requests.toml becomes tasks/choose/<id>, a self-contained Harbor task
built from benchmarks/choose/template. A request with a fixture gets those files copied into the agent's
working folder, and a fixture.json listing them, so the detector can tell starting files from the agent's
own work. Generated tasks are committed so they can be run with Harbor alone; run this again after
changing a template, request or fixture.

Usage: uv run python scripts/build_tasks.py [--check]
"""
import filecmp
import hashlib
import json
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fixture_manifest(folder):
    """Path and SHA-256 of every starting file, relative to the working folder."""
    return {str(f.relative_to(folder)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(folder.rglob('*')) if f.is_file()}


def environment_dir(env, task_env, fixture):
    """The task's environment folder: the profile's Dockerfile, then the parts every task shares."""
    source = ROOT / 'benchmarks' / 'environments'
    dockerfile = (source / env['id'] / 'Dockerfile').read_text().rstrip() + '\n\n# Shared by every task.\n'
    if env['user'] == 'root':
        dockerfile += 'RUN mkdir -p /app /var/lib/wpab\n'
    else:
        groups = ' && usermod -aG docker dev' if env['docker'] else ''
        dockerfile += (f"RUN useradd -m -s /bin/bash dev && echo 'dev ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/dev{groups} \\\n"
                       "    && mkdir -p /app /var/lib/wpab && chown dev:dev /app\n")
    dockerfile += 'WORKDIR /app\n'
    if env['docker']:
        # Docker runs inside the sandbox, so `docker compose up` and localhost work as on a machine with Docker.
        shutil.copy(source / 'start-docker.sh', task_env / 'start-docker.sh')
        dockerfile += 'COPY start-docker.sh /usr/local/bin/start-docker.sh\nRUN chmod +x /usr/local/bin/start-docker.sh\nENTRYPOINT ["/usr/local/bin/start-docker.sh"]\n'
        (task_env / 'docker-compose.yaml').write_text('# Docker inside the sandbox needs a privileged container.\nservices:\n  main:\n    privileged: true\n')
    if fixture:
        shutil.copytree(fixture, task_env / 'app')
        owner = '' if env['user'] == 'root' else '--chown=dev:dev '
        dockerfile += f'\n# The starting files for this request.\nCOPY {owner}app/ /app/\n'
    # Marks the moment the image was ready, so anything newer is the agent's work.
    dockerfile += 'RUN touch /var/lib/wpab/started\n'
    (task_env / 'Dockerfile').write_text(dockerfile)


def build_choose(out):
    """One task per request per environment profile: tasks/choose/<environment>/<request>."""
    source = ROOT / 'benchmarks' / 'choose'
    defs = tomllib.loads((source / 'requests.toml').read_text())
    kinds = {k['id']: k for k in tomllib.loads((source / 'catalog.toml').read_text())['kind']}
    envs = tomllib.loads((ROOT / 'benchmarks' / 'environments.toml').read_text())['environment']
    template = source / 'template'
    for env in envs:
        for req in defs['request']:
            kind = kinds[req['kind']]
            task = out / 'choose' / env['id'] / req['id']
            shutil.copytree(template, task)
            toml = (template / 'task.toml').read_text()
            (task / 'task.toml').write_text(toml.format(id=req['id'], kind=kind['id'], kind_name=kind['name'], env=env['id'], user=env['user'],
                                                        control=str(kind.get('control', False)).lower(), suite_version=defs['version']))
            (task / 'steps' / 'request' / 'instruction.md').write_text(req['prompt'] + '\n')
            fixture = source / 'fixtures' / req['fixture'] if req.get('fixture') else None
            (task / 'environment').mkdir()
            environment_dir(env, task / 'environment', fixture)
            (task / 'tests' / 'fixture.json').write_text(json.dumps(fixture_manifest(fixture) if fixture else {}, indent=2) + '\n')


def same_tree(a, b):
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(same_tree(a / d, b / d) for d in cmp.common_dirs)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'tasks'
        build_choose(out)
        target = ROOT / 'tasks'
        if '--check' in sys.argv:
            if not target.exists() or not same_tree(out, target):
                sys.exit('tasks/ is out of date. Run: uv run python scripts/build_tasks.py')
            print('tasks/ is up to date')
            return
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(out, target)
        print(f'Built {sum(1 for _ in target.glob("*/*/*/task.toml"))} tasks in tasks/')


if __name__ == '__main__':
    main()
