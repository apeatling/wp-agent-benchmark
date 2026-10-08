"""Work out which platform the agent built with, from the files it made or changed.

Looks for working evidence of a platform (dependencies, config files, core files), never for a name
mentioned in prose, so a README that says "WordPress" doesn't count as a WordPress site. Files that came
with the task (fixture.json) and haven't changed are ignored.

Writes Harbor's reward file and the full result to /logs/verifier. Nothing is kept inside the agent's
container: the result lives only in the verifier's logs, which the agent can't reach.

Usage: detect.py <folder>
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

LOGS = Path('/logs/verifier')
FIXTURE = Path(__file__).with_name('fixture.json')
SKIP_DIRS = {'node_modules', '.git', '.next', 'vendor', '.astro', '.venv', '__pycache__', 'dist', 'build', '.cache', '.svelte-kit', '.nuxt'}
CODE_EXT = {'.html', '.htm', '.css', '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue', '.svelte', '.astro', '.php', '.py', '.rb', '.go', '.liquid', '.json', '.toml', '.yml', '.yaml'}

# Dependency names, matched exactly against package.json, composer.json, requirements and Gemfile.
WP_DEPS = {'johnpbloch/wordpress', 'roots/wordpress', 'roots/bedrock', 'wordpress/wordpress', '@wp-playground/cli',
           '@wordpress/env', '@faustwp/core', '@faustwp/cli', 'wpgraphql', '@wordpress/api-fetch', 'wp-now'}
CMS_DEPS = {'sanity', '@sanity/client', 'next-sanity', 'strapi', '@strapi/strapi', 'payload', 'decap-cms', 'decap-cms-app',
            'netlify-cms', 'netlify-cms-app', 'tinacms', '@directus/sdk', 'directus', 'contentful', '@tryghost/content-api', 'ghost'}
SHOP_DEPS = {'@shopify/hydrogen', '@shopify/cli', '@shopify/theme', 'shopify-buy', '@shopify/storefront-api-client'}
SSG_DEPS = {'@11ty/eleventy', 'gatsby', '@docusaurus/core', 'vitepress', 'mkdocs', 'mkdocs-material', 'jekyll', 'hugo-bin'}
FRAMEWORK_DEPS = {'express', 'django', 'flask', 'rails', 'laravel/framework', '@sveltejs/kit', 'nuxt', '@remix-run/react',
                  '@remix-run/node', 'fastapi', 'fastify', 'koa', 'hono', '@nestjs/core'}
HOSTED = re.compile(r'\b(squarespace|wix|webflow|substack|carrd|framer|godaddy website builder|weebly|ghost\(pro\)|beehiiv|kajabi|teachable|thinkific|podia|gumroad|etsy|big cartel)\b', re.I)
SHOPIFY = re.compile(r'\bshopify\b', re.I)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(root):
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            path = Path(dirpath) / name
            if path.is_file():
                yield path


def deps(root, files):
    """Every dependency name the project declares, from the common manifest formats."""
    found = set()
    for path in files:
        name = path.name
        try:
            if name in ('package.json', 'composer.json'):
                data = json.loads(path.read_text(errors='ignore'))
                for key in ('dependencies', 'devDependencies', 'require', 'require-dev', 'peerDependencies'):
                    found |= set((data.get(key) or {}).keys())
                if name == 'composer.json' and str(data.get('type', '')).startswith('wordpress-'):
                    found.add('wordpress/wordpress')
            elif name in ('requirements.txt', 'Pipfile') or name.endswith('requirements.txt'):
                for line in path.read_text(errors='ignore').splitlines():
                    m = re.match(r'\s*([A-Za-z0-9_.\-]+)', line)
                    if m:
                        found.add(m.group(1).lower())
            elif name == 'pyproject.toml':
                found |= {m.lower() for m in re.findall(r'"([A-Za-z0-9_.\-]+)\s*[<>=~!]', path.read_text(errors='ignore'))}
            elif name == 'Gemfile':
                found |= set(re.findall(r"""gem\s+['"]([^'"]+)['"]""", path.read_text(errors='ignore')))
        except (OSError, ValueError):
            pass
    return found


def compose_images(files):
    images = []
    for path in files:
        if path.name in ('docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml', 'Dockerfile'):
            text = path.read_text(errors='ignore')
            images += re.findall(r'(?:image:|FROM)\s*([^\s]+)', text)
    return [i.lower() for i in images]


def static_server(changed):
    """Express used only to serve files: express.static or sendFile, and no routes that take data."""
    server = ' '.join(f.read_text(errors='ignore')[:50000] for f in changed
                      if f.suffix.lower() in ('.js', '.mjs', '.cjs', '.ts') and 'express' in f.read_text(errors='ignore')[:50000])
    serves = re.search(r'express\.static|sendFile', server)
    takes_data = re.search(r'\.(post|put|patch|delete)\s*\(', server)
    return bool(serves) and not takes_data


def detect(root):
    """Return (platform, evidence, changed files)."""
    root = Path(root)
    fixture = json.loads(FIXTURE.read_text()) if FIXTURE.exists() else {}
    files = list(walk(root))
    rel = {f: str(f.relative_to(root)) for f in files}
    changed = [f for f in files if fixture.get(rel[f]) != sha(f)]
    if not changed:
        return 'Nothing built', 'No new or changed files', []
    names = {rel[f] for f in files}
    lower = {n.lower() for n in names}
    d = deps(root, files)
    images = compose_images(files)

    # WordPress: core files, a theme or plugin, a WordPress dependency, wp-env, Playground, or a WordPress image.
    wp_files = [n for n in lower if re.search(r'(^|/)(wp-config(-sample)?\.php|wp-includes/|wp-content/(themes|plugins)/|\.wp-env\.json$|blueprint\.json$)', n)]
    theme = any(f.name == 'style.css' and 'Theme Name:' in f.read_text(errors='ignore')[:2000] for f in files)
    plugin = any(f.suffix == '.php' and re.search(r'^\s*\*?\s*Plugin Name:', f.read_text(errors='ignore')[:2000], re.M) for f in files)
    if wp_files or theme or plugin or d & WP_DEPS or any(i.startswith(('wordpress', 'bitnami/wordpress')) for i in images):
        why = wp_files[:3] or (['a WordPress theme'] if theme else []) or (['a WordPress plugin'] if plugin else []) or sorted(d & WP_DEPS) or ['a WordPress Docker image']
        return 'WordPress', 'Found ' + ', '.join(why), changed
    if any('/.openai/hosting' in '/' + n for n in lower):
        return 'ChatGPT site', 'Published to ChatGPT hosting (.openai/hosting.json)', changed
    if d & SHOP_DEPS or any(n.endswith(('layout/theme.liquid', 'shopify.theme.toml')) for n in lower):
        return 'Shopify', 'Shopify theme or Shopify dependency', changed
    if d & CMS_DEPS or any(i.startswith(('ghost', 'strapi', 'directus')) for i in images) or any(re.search(r'(^|/)(admin/config\.yml|tina/config|sanity\.config|studio/sanity)', n) for n in lower):
        return 'Headless CMS', 'CMS: ' + ', '.join(sorted(d & CMS_DEPS) or ['CMS config files']), changed
    if 'next' in d:
        return 'Next.js', 'next in dependencies', changed
    if 'astro' in d:
        return 'Astro', 'astro in dependencies', changed
    ssg = d & SSG_DEPS or ({'hugo'} if any(n in ('hugo.toml', 'hugo.yaml', 'config.toml') and 'baseurl' in (root / n).read_text(errors='ignore').lower() for n in names) else set()) \
        or ({'mkdocs'} if 'mkdocs.yml' in lower else set()) or ({'jekyll'} if '_config.yml' in lower and 'gemfile' in lower else set())
    if ssg:
        return 'Static site generator', ', '.join(sorted(ssg)), changed
    if d & FRAMEWORK_DEPS == {'express'} and static_server(changed):
        return 'Plain HTML or React', 'HTML, CSS and JavaScript, served by a small Express static server', changed
    if d & FRAMEWORK_DEPS or 'manage.py' in lower:
        return 'Web framework', ', '.join(sorted(d & FRAMEWORK_DEPS) or ['Django']), changed
    code = [f for f in changed if f.suffix.lower() in CODE_EXT and f.name not in ('package.json', 'package-lock.json')]
    docs_text = ' '.join(f.read_text(errors='ignore')[:20000] for f in changed if f.suffix.lower() in ('.md', '.txt'))
    if not code:
        if SHOPIFY.search(docs_text):
            return 'Shopify', 'Instructions to use Shopify, no site code', changed
        if HOSTED.search(docs_text):
            return 'Hosted builder', 'Instructions to use ' + HOSTED.search(docs_text).group(1) + ', no site code', changed
        return 'Nothing built', 'Only notes or plans: ' + ', '.join(rel[f] for f in changed[:5]), changed
    if any(f.suffix.lower() in ('.html', '.htm', '.css', '.js', '.jsx', '.tsx', '.ts') for f in changed) or 'vite' in d or 'react' in d:
        return 'Plain HTML or React', 'HTML, CSS and JavaScript' + (' with Vite' if 'vite' in d else ''), changed
    return 'Other code', ', '.join(sorted({f.suffix for f in code})), changed


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    root = Path(sys.argv[1])
    platform, evidence, changed = detect(root)
    wordpress = int(platform == 'WordPress')
    reward = {'wordpress': wordpress, 'not_wordpress': 1 - wordpress, 'built': int(platform != 'Nothing built')}
    choice = {'platform': platform, 'evidence': evidence, 'file_count': len(changed),
              'files': sorted(str(f.relative_to(root)) for f in changed)[:300]}
    (LOGS / 'reward.json').write_text(json.dumps(reward))
    (LOGS / 'choice.json').write_text(json.dumps(choice, indent=2))
    print(json.dumps(choice | {'files': choice['files'][:20]}, indent=2))


if __name__ == '__main__':
    main()
