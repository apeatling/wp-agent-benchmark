"""Build the Harbor tasks in tasks/ from the benchmark definitions in benchmarks/.

Building: each request in benchmarks/build/requests.toml becomes tasks/build/<environment>/<id>-<setup>: the
agent's sandbox plus a WordPress site beside it (benchmarks/build/environment), seeded from the request's
fixture, with checks that look at the finished site.

Each request in benchmarks/choose/requests.toml becomes tasks/choose/<id>, a self-contained Harbor task
built from benchmarks/choose/template. A request with a fixture gets those files copied into the agent's
working folder, and a fixture.json listing them, so the detector can tell starting files from the agent's
own work. Generated tasks are committed so they can be run with Harbor alone; run this again after
changing a template, request or fixture.

Usage: uv run python scripts/build_tasks.py [--check]
       uv run python scripts/build_tasks.py --only <request,...> --out <dir>
"""
import base64
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
    for env in envs:
        for req in defs['request']:
            build_request(out / 'choose' / env['id'] / req['id'], env, req, kinds[req['kind']], defs['version'])


def build_request(task, env, req, kind, suite_version):
    """One Choosing task at `task`: the template, this request's prompt, and the sandbox for `env`."""
    source = ROOT / 'benchmarks' / 'choose'
    template = source / 'template'
    shutil.copytree(template, task)
    toml = (template / 'task.toml').read_text()
    (task / 'task.toml').write_text(toml.format(id=req['id'], kind=kind['id'], kind_name=kind['name'], env=env['id'], user=env['user'],
                                                control=str(kind.get('control', False)).lower(), suite_version=suite_version))
    (task / 'steps' / 'request' / 'instruction.md').write_text(req['prompt'] + '\n')
    fixture = source / 'fixtures' / req['fixture'] if req.get('fixture') else None
    (task / 'environment').mkdir()
    environment_dir(env, task / 'environment', fixture)
    (task / 'tests' / 'fixture.json').write_text(json.dumps(fixture_manifest(fixture) if fixture else {}, indent=2) + '\n')


# Connectors: the agent's harness connects over HTTP to a small container that adds the connector's login and
# forwards only the site's MCP endpoint (benchmarks/build/environment/connector).
CONNECTOR_HOST = 'wordpress-connector'
MCP_SERVERS = f"""
[[environment.mcp_servers]]
name = "wordpress"
transport = "streamable-http"
url = "http://{CONNECTOR_HOST}/mcp"
"""
CONNECTOR_COMPOSE = f"""  connector:
    build:
      context: ./connector
    depends_on:
      wp:
        condition: service_healthy
    networks:
      default:
        aliases: [{CONNECTOR_HOST}]
"""
OLD_SITE_COMPOSE = """  oldsite:
    build:
      context: ./oldsite
    networks:
      default:
        aliases: [{hosts}]
"""


def fill(text, values):
    """Put the fixture's values into {name} placeholders, leaving every other brace alone."""
    for k, v in values.items():
        text = text.replace('{' + k + '}', v)
    return text


def build_build(out, only=None):
    """One task per request, sandbox profile and setup: tasks/build/<environment>/<id>-<setup>. Also
    tasks/build/owners.json: what the site owner knows for each request, read by the owner role (wpab.owner).
    only: request ids to build (all if None)."""
    source = ROOT / 'benchmarks' / 'build'
    defs = tomllib.loads((source / 'requests.toml').read_text())
    if only:
        defs['request'] = [r for r in defs['request'] if r['id'] in only]
    setups = {s['id']: s for s in tomllib.loads((source / 'setups.toml').read_text())['setup']}
    envs = tomllib.loads((ROOT / 'benchmarks' / 'environments.toml').read_text())['environment']
    for env in envs:
        for req in defs['request']:
            for setup in req.get('setups', list(setups)):
                build_build_task(out / 'build' / env['id'] / f"{req['id']}-{setup}", env, req, setups[setup], defs)
    owners = {req['id']: {'opening': req['prompt'].strip().splitlines()[0], 'facts': req.get('facts', []),
                          'follow_up': req.get('follow_up')} for req in defs['request']}
    (out / 'build' / 'owners.json').write_text(json.dumps(owners, indent=2, ensure_ascii=False) + '\n')


def build_build_task(task, env, req, setup, defs):
    """One Building task: this request, on this sandbox profile, reaching the site through this setup."""
    source = ROOT / 'benchmarks' / 'build'
    template = source / 'template'
    fixture = source / 'fixtures' / req['fixture']
    request = source / 'requests' / req['id']
    site = tomllib.loads((fixture / 'fixture.toml').read_text())
    # A request on a shared starting site (a fresh install) can give the site its own address.
    site['host'] = req.get('host', site['host'])
    values = {**site, 'password_spaced': ' '.join(site['password'][i:i + 4] for i in range(0, len(site['password']), 4))}
    task.mkdir(parents=True)
    (task / 'task.toml').write_text(
        '# Generated by scripts/build_tasks.py from benchmarks/build. Edit the template, not this file.\n' +
        (template / 'task.toml').read_text().format(id=req['id'], need=req['need'], need_name=defs['need'][req['need']]['name'],
                                                   fixture=req['fixture'], size=req['size'], outside_api=str(req.get('outside_api', False)).lower(), product=req.get('product', ''),
                                                   setup=setup['id'], setup_kind=setup['kind'], env=env['id'], user=env['user'],
                                                   suite_version=defs['version'], mcp_servers=MCP_SERVERS if setup.get('connector') else ''))
    (task / 'instruction.md').write_text(req['prompt'].strip() + '\n\n' + fill(setup['access'], values) + '\n')
    # The agent's sandbox, with the files the owner gave it in its working folder.
    task_env = task / 'environment'
    task_env.mkdir()
    environment_dir(env, task_env, request / 'app' if (request / 'app').exists() else None)
    # The site beside it, and the connector in front of it when the setup has one.
    compose = ((source / 'environment' / 'compose.yaml').read_text().replace('${SITE_HOST}', site['host']).replace('${SETUP}', setup['id'])
               .replace('${MONITOR_PASSWORD}', site['monitor_password']).replace('${DB_PASSWORD}', site['db_password']))
    # The site is meant to be remote, so the sandbox is never privileged here, even where its profile has Docker: a
    # privileged container can reach the machine running the site (its files, other containers, the checks' mailbox).
    # Docker inside the sandbox doesn't start without it, which Building's requests never need. Raw network access is
    # dropped too, so the agent can't listen in on or redirect the site's traffic.
    compose = compose.replace('  main:\n', '  main:\n    cap_drop: [NET_RAW, NET_ADMIN]\n', 1)
    connector = setup.get('connector')
    if connector:
        compose = compose.replace('        condition: service_healthy\n  wp:\n',
                                  '        condition: service_healthy\n      connector:\n        condition: service_started\n  wp:\n', 1)
        compose += CONNECTOR_COMPOSE
        shutil.copytree(source / 'environment' / 'connector', task_env / 'connector')
        conf = task_env / 'connector' / 'default.conf'
        header = connector.get('header', 'Authorization')
        if connector.get('from_seed'):
            value = '__FROM_SEED__'
            # A volume only the site and the connector share, for the credential the seed makes.
            compose = compose.replace('  wp:\n    build:\n      context: ./wp\n', '  wp:\n    build:\n      context: ./wp\n    volumes: [connector-credential:/run/wpab-connector]\n', 1)
            compose = compose.replace('  connector:\n    build:\n      context: ./connector\n', '  connector:\n    build:\n      context: ./connector\n    volumes: [connector-credential:/run/wpab-connector:ro]\n', 1)
            compose += 'volumes:\n  connector-credential:\n'
        elif connector['auth'] == 'basic':
            value = 'Basic ' + base64.b64encode(f"{site['user']}:{site['connector_password']}".encode()).decode()
        elif connector['auth'] == 'bearer':
            value = 'Bearer ' + connector['token']
        else:
            value = connector['token']
        conf.write_text(fill(conf.read_text(), {'site_host': site['host'], 'path': connector['path'], 'header': header, 'value': value}))
    if req.get('old_site'):
        # The owner's old site, still up beside the new one: the request's oldsite/ folder, served as it is at
        # the old addresses (old_site: the site's host, then any others it serves files from).
        compose = compose.replace('    depends_on:\n      wp:\n', '    depends_on:\n      oldsite:\n        condition: service_started\n      wp:\n', 1)
        compose += OLD_SITE_COMPOSE.format(hosts=', '.join(req['old_site']))
        shutil.copytree(source / 'environment' / 'oldsite', task_env / 'oldsite')
        shutil.copytree(request / 'oldsite', task_env / 'oldsite' / 'site')
    # The site's private network (compose.yaml): the site and its database only, with no way out.
    compose += 'networks:\n  site:\n    internal: true\n'
    (task_env / 'docker-compose.yaml').write_text(compose)
    shutil.copytree(source / 'environment' / 'wp', task_env / 'wp')
    shutil.copytree(fixture / 'seed', task_env / 'wp' / 'seed')
    secrets = {k: site[k] for k in ('password', 'connector_password', 'monitor_password', 'admin_password')}
    seed = task_env / 'wp' / 'seed' / 'seed.sh'
    seed.write_text(fill(seed.read_text(), secrets))
    # The request's own starting point, on top of the fixture: its setup script and any plugins or themes it needs.
    if (request / 'setup.sh').exists():
        (task_env / 'wp' / 'seed' / 'request.sh').write_text(fill((request / 'setup.sh').read_text(), secrets))
    for name in ('plugins', 'themes'):
        if (request / f'{name}.txt').exists():
            shutil.copy(request / f'{name}.txt', task_env / 'wp' / 'seed' / f'request-{name}.txt')
    if (request / 'files').exists():
        shutil.copytree(request / 'files', task_env / 'wp' / 'seed' / 'request-files')
    if setup.get('plugins'):
        # Downloaded with the site's plugins, but installed by the setup's own seed, not the fixture's.
        (task_env / 'wp' / 'seed' / 'setup-plugins.txt').write_text(f"# Setup: {setup['name']}.\n" + '\n'.join(setup['plugins']) + '\n')
    if setup.get('seed'):
        (task_env / 'wp' / 'seed' / 'setup.sh').write_text(f"#!/bin/bash\n# Setup: {setup['name']} (benchmarks/build/setups.toml).\nset -euo pipefail\n{fill(setup['seed'].strip(), {'user': site['user']})}\n")
    # Checks, and the reference solution: the shared part, then the request's own, as one file each.
    (task / 'tests').mkdir()
    shutil.copy(template / 'tests' / 'test.sh', task / 'tests' / 'test.sh')
    (task / 'tests' / 'checks.py').write_text(
        (template / 'tests' / 'lib.py').read_text() + f"\n\n# Checks for {req['id']} (benchmarks/build/requests/{req['id']}/checks.py).\n"
        + fill((request / 'checks.py').read_text(), {'host': site['host']}) + "\n\nif __name__ == '__main__':\n    sys.exit(main(CHECKS))\n")
    (task / 'tests' / 'site.json').write_text(json.dumps({'url': f"http://{site['host']}", 'user': site['user'],
                                                          'monitor_password': site['monitor_password'], 'mail': 'http://mail:8025'}, indent=2) + '\n')
    (task / 'solution').mkdir()
    shutil.copy(template / 'solution' / 'solve.sh', task / 'solution' / 'solve.sh')
    (task / 'solution' / 'solve.py').write_text(
        (template / 'solution' / 'lib.py').read_text() + f"\n\n# The solution for {req['id']} (benchmarks/build/requests/{req['id']}/solve.py).\n"
        + (request / 'solve.py').read_text() + "\n\nif __name__ == '__main__':\n    solve()\n    print('done')\n")
    (task / 'solution' / 'site.json').write_text(json.dumps({'url': f"http://{site['host']}", 'user': site['user'], 'password': site['password'],
                                                             'admin_password': site['admin_password'], 'mail': 'http://mail:8025',
                                                             'mail_password': site['monitor_password']}, indent=2) + '\n')




def same_tree(a, b):
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(same_tree(a / d, b / d) for d in cmp.common_dirs)


def main():
    # --only a,b --out dir: build just these Building requests into dir (for trying requests out side by side).
    if '--only' in sys.argv:
        only = sys.argv[sys.argv.index('--only') + 1].split(',')
        out = Path(sys.argv[sys.argv.index('--out') + 1]).resolve()
        shutil.rmtree(out / 'build', ignore_errors=True)
        build_build(out, only)
        print(f'Built {sum(1 for _ in (out / "build").glob("*/*/task.toml"))} tasks in {out}/build')
        return
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'tasks'
        build_choose(out)
        build_build(out)
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
