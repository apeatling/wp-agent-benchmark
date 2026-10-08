"""The overnight loop: limits wait and resume, a broken environment stops an agent, finished agents end.
Harbor, Jev and the site build are mocked."""
import argparse
import collections
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from wpab import cli, defs


class Overnight(unittest.TestCase):
    def test_loop(self):
        left = {'gpt-6-1-sol-codex': ['a', 'b', 'c', 'd'], 'gemini-3-8-flash-antigravity': ['a', 'b'], 'opus-5-5-claude-code': ['a']}
        calls = collections.defaultdict(int)

        sizes = collections.defaultdict(list)

        def fake_run(benchmark, batch, agent, auth, chunk, **kw):
            calls[agent['id']] += 1
            sizes[agent['id']].append(len(chunk))
            if agent['id'] == 'opus-5-5-claude-code':
                return collections.Counter({'infra_error': 1})  # Docker is broken for this one
            if agent['id'] == 'gpt-6-1-sol-codex' and calls[agent['id']] == 1:
                return collections.Counter({'limit_reached': 1})  # first job hits the plan's limit
            for t in chunk:
                left[agent['id']].remove(t)
            return collections.Counter({'completed': len(chunk)})

        args = argparse.Namespace(benchmark='choose', batch='2026-10', repeats=2, until='23:59', wait=30, plan_chunk=3, plan_concurrent=1, concurrent=3, env='docker',
                                  agents='gpt-6-1-sol-codex:plan,gemini-3-8-flash-antigravity:api,opus-5-5-claude-code:api')
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(defs, 'JOBS', Path(tmp)), mock.patch.object(defs, 'DATA', Path(tmp) / 'data'), mock.patch.object(defs, 'OUT', Path(tmp) / 'data'), \
                mock.patch.object(cli, 'auth_env', return_value={}), mock.patch.object(cli, 'preflight'), mock.patch.object(cli, 'run_agent', side_effect=fake_run), \
                mock.patch.object(cli, 'remaining', side_effect=lambda b, ba, a, r: list(left[a])), \
                mock.patch.object(cli.time, 'sleep') as sleep, mock.patch.object(cli.subprocess, 'Popen'), \
                mock.patch.object(cli.sitedata, 'build', return_value={'runs': []}), mock.patch.object(cli.classifier, 'classify', return_value=[]), \
                mock.patch.object(cli.reviewer, 'review', return_value=[]), mock.patch.dict('os.environ', {}, clear=False):
            cli.os.environ.pop('TYPESAFE_API_KEY', None)
            cli.overnight(args)
            log = next(Path(tmp).glob('overnight-*.log')).read_text()
        self.assertEqual(left['gpt-6-1-sol-codex'], [])
        self.assertEqual(left['gemini-3-8-flash-antigravity'], [])
        self.assertEqual(sleep.call_count, 1)  # waited once after the limit
        self.assertEqual(calls['opus-5-5-claude-code'], 3)  # gave up after three empty jobs
        self.assertIn('stopped after 3 jobs in a row', log)
        self.assertEqual(sizes['gpt-6-1-sol-codex'][:2], [3, 3])  # plan runs go three at a time
        self.assertEqual(sizes['gemini-3-8-flash-antigravity'], [2])  # API runs go all at once
        self.assertIn('usage limit, waiting until', log)


if __name__ == '__main__':
    unittest.main()
