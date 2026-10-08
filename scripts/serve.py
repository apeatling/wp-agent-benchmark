"""Serve site/ locally the way Spacefast does: clean URLs, so /choose/runs serves choose/runs.html.

    uv run python scripts/serve.py [port]            the published results
    uv run python scripts/serve.py --local [port]    your own runs, from `wpab site` (site/data-local/)
"""
import functools
import http.server
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')


LOCAL = '--local' in sys.argv


class CleanURLs(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if LOCAL and path.startswith('/data/'):
            path = '/data-local/' + path[len('/data/'):]
        local = super().translate_path(path)
        if not os.path.exists(local) and os.path.exists(local + '.html'):
            return local + '.html'
        return local


if __name__ == '__main__':
    ports = [a for a in sys.argv[1:] if a.isdigit()]
    port = int(ports[0]) if ports else 4173
    if LOCAL and not os.path.isdir(os.path.join(ROOT, 'data-local')):
        sys.exit('No local site data yet. Run some agents, then `uv run wpab classify` and `uv run wpab site`.')
    print(f"Serving {'your local runs' if LOCAL else 'the published results'} at http://localhost:{port}/choose/")
    handler = functools.partial(CleanURLs, directory=ROOT)
    http.server.ThreadingHTTPServer(('', port), handler).serve_forever()
