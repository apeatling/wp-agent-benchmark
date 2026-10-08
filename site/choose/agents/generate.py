# Writes one page per agent at /choose/agents/<agent id>/index.html from _template.html, for every agent
# in benchmarks/agents.toml. Run it after changing the template or the agents:
#   python3 site/choose/agents/generate.py
import os
import re
import shutil
import tomllib

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, '..', '..', '..'))
agents = tomllib.load(open(os.path.join(root, 'benchmarks', 'agents.toml'), 'rb'))['agent']
template = open(os.path.join(here, '_template.html')).read()
# The template's {{ID}} is the short key the pages use (opus, gpt, qwen…), made as in src/wpab/site.py.
key = lambda a: re.sub(r'[^a-z].*', '', a['name'].lower())
ids = {a['id'] for a in agents}
for name in os.listdir(here):  # pages for agents no longer listed
    if os.path.isdir(os.path.join(here, name)) and name not in ids:
        shutil.rmtree(os.path.join(here, name))
for a in agents:
    d = os.path.join(here, a['id'])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w').write(template.replace('{{ID}}', key(a)))
    print(d)
