"""The Choosing detector: real projects are named correctly, and mentions of a name don't count.

Run with: uv run python -m unittest discover tests
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('detect', ROOT / 'benchmarks/choose/template/tests/detect.py')
detect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(detect)


def project(files, fixture=None):
    """A temporary project folder with these files, and optionally a fixture manifest."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name) / 'app'
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    manifest = Path(tmp.name) / 'fixture.json'
    manifest.write_text(json.dumps({name: detect.sha(root / name) for name in (fixture or [])}))
    detect.FIXTURE = manifest
    return tmp, root


class Detect(unittest.TestCase):
    def check(self, files, expected, fixture=None):
        tmp, root = project(files, fixture)
        with tmp:
            platform, evidence, _ = detect.detect(root)
        self.assertEqual(platform, expected, evidence)

    def test_wordpress_core(self):
        self.check({'wp-config.php': '<?php', 'wp-content/themes/x/style.css': '/* Theme Name: X */'}, 'WordPress')

    def test_wordpress_playground_and_env(self):
        self.check({'blueprint.json': '{"steps": []}'}, 'WordPress')
        self.check({'.wp-env.json': '{}'}, 'WordPress')
        self.check({'package.json': '{"devDependencies": {"@wp-playground/cli": "^1"}}'}, 'WordPress')

    def test_wordpress_compose(self):
        self.check({'docker-compose.yml': 'services:\n  wp:\n    image: wordpress:6-apache\n'}, 'WordPress')

    def test_headless_wordpress(self):
        self.check({'package.json': '{"dependencies": {"next": "15", "@faustwp/core": "3"}}'}, 'WordPress')

    def test_readme_mention_is_not_wordpress(self):
        self.check({'README.md': 'You could also use WordPress for this.', 'index.html': '<h1>Hi</h1>'}, 'Plain HTML or React')
        self.check({'package.json': '{"dependencies": {"next": "15"}, "description": "not wordpress"}'}, 'Next.js')

    def test_frameworks(self):
        self.check({'package.json': '{"dependencies": {"astro": "5"}}'}, 'Astro')
        self.check({'package.json': '{"devDependencies": {"@11ty/eleventy": "3"}}'}, 'Static site generator')
        self.check({'package.json': '{"dependencies": {"express": "5"}}', 'server.js': ''}, 'Web framework')
        self.check({'package.json': '{"devDependencies": {"vite": "6"}, "dependencies": {"react": "19"}}', 'src/App.jsx': ''}, 'Plain HTML or React')

    def test_cms_and_shop(self):
        self.check({'package.json': '{"dependencies": {"next": "15", "next-sanity": "9"}}'}, 'Headless CMS')
        self.check({'admin/config.yml': 'backend: git', 'index.html': ''}, 'Headless CMS')
        self.check({'layout/theme.liquid': ''}, 'Shopify')

    def test_hosted_recommendation(self):
        self.check({'SETUP.md': 'Sign up for Squarespace and pick the Bakery template.'}, 'Hosted builder')
        self.check({'PLAN.md': 'Use Shopify Basic and import the candles.'}, 'Shopify')
        self.check({'BLOG-STARTER.md': 'Writing prompts and a launch checklist.'}, 'Nothing built')
        self.check({'.openai/hosting.json': '{}', 'ASSETS.md': 'images'}, 'ChatGPT site')
        self.check({'site/.openai/hosting.json': '{}', 'site/index.html': '<p>hi</p>'}, 'ChatGPT site')

    def test_express_static_server_is_plain_html(self):
        pkg = '{"dependencies": {"express": "^4"}}'
        self.check({'package.json': pkg, 'index.html': '<p>hi</p>',
                    'server.js': "const express = require('express'); app.use(express.static('public'));"}, 'Plain HTML or React')
        self.check({'package.json': pkg, 'index.html': '<p>hi</p>',
                    'server.js': "const express = require('express'); app.use(express.static('public')); app.post('/api/orders', h);"}, 'Web framework')

    def test_nothing_and_fixture(self):
        self.check({}, 'Nothing built')
        # Untouched starting files aren't the agent's work.
        self.check({'index.html': '<h1>Cafe</h1>'}, 'Nothing built', fixture=['index.html'])

    def test_fixture_edited_in_place(self):
        tmp, root = project({'index.html': '<h1>Cafe</h1>', 'menu.html': '<ul></ul>'}, fixture=['index.html', 'menu.html'])
        with tmp:
            (root / 'menu.html').write_text('<ul><li>New</li></ul>')
            platform, _, changed = detect.detect(root)
        self.assertEqual(platform, 'Plain HTML or React')
        self.assertEqual([p.name for p in changed], ['menu.html'])


if __name__ == '__main__':
    unittest.main()
