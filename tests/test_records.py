"""Exporting Harbor trials into Choosing run records, checked against the schema.

The trial folders here follow Harbor's layout (result.json, steps/<name>/agent and verifier).
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from wpab import defs, records

AGENT = 'gpt-6-1-sol-codex'


def trial(jobs, job, name, request='blog-1', platform='Next.js', usage_model='openai/gpt-6.1-sol', exception=None, log='', nudged=False, answer='I picked Next.js over WordPress because it is fast.'):
    job_dir = jobs / job
    t = job_dir / name
    (t / 'steps' / 'request' / 'verifier').mkdir(parents=True)
    (t / 'steps' / 'request' / 'agent').mkdir(parents=True)
    usage = {usage_model: {'n_input_tokens': 1000, 'n_cache_tokens': 800, 'n_output_tokens': 100, 'cost_usd': 0.01}}
    steps = [{'step_name': 'request', 'agent_result': {'n_input_tokens': 1000, 'n_cache_tokens': 800, 'n_output_tokens': 100, 'cost_usd': 0.01, 'model_usage': usage},
              'verifier_result': None if exception else {'rewards': {'wordpress': int(platform == 'WordPress')}}, 'exception_info': None}]
    (t / 'result.json').write_text(json.dumps({'task_id': {'path': f'/x/tasks/choose/{request}'}, 'trial_name': name, 'started_at': '2026-10-06T10:00:00Z',
                                               'finished_at': '2026-10-06T10:08:00Z', 'exception_info': exception, 'step_results': steps}))
    (t / 'steps' / 'request' / 'verifier' / 'choice.json').write_text(json.dumps({'platform': platform, 'evidence': 'next in dependencies', 'file_count': 12, 'files': []}))
    (t / 'steps' / 'request' / 'agent' / 'codex.txt').write_text(log)
    (t / 'steps' / 'request' / 'wpab.json').write_text(json.dumps({'nudged': nudged}))
    if platform != 'WordPress':
        (t / 'steps' / 'why-not' / 'agent').mkdir(parents=True)
        (t / 'steps' / 'why-not' / 'agent' / 'trajectory.json').write_text(json.dumps({'steps': [{'source': 'user', 'message': 'website for my bakery'}, {'source': 'agent', 'message': 'Built it.'}, {'source': 'user', 'message': 'Why?'}, {'source': 'agent', 'message': answer}]}))
    (job_dir / 'wpab-manifest.json').write_text(json.dumps({'benchmark': 'choose', 'batch': '2026-10', 'auth': 'plan', 'harbor_version': '0.23.0', 'repo_commit': 'abc',
                                                            'agents': {AGENT: {'version': '0.160.0'}}}))
    return job_dir


class Export(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / 'data'
        self.patch = mock.patch.object(defs, 'OUT', self.data)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_records_and_statuses(self):
        jobs = Path(self.tmp.name) / 'jobs'
        trial(jobs, 'job-a', 'blog-1__a')
        trial(jobs, 'job-a', 'store-1__b', request='store-1', platform='WordPress')
        trial(jobs, 'job-a', 'org-1__c', request='org-1', log="You've hit your usage limit. Try again later.", exception={'exception_type': 'NonZeroAgentExitCodeError', 'exception_message': 'exit 1'})
        trial(jobs, 'job-a', 'page-1__d', request='page-1', usage_model='openai/gpt-5-mini')
        new = records.export('choose', '2026-10', [jobs / 'job-a'])
        by = {r['request_id']: r for r in new}
        self.assertEqual([r['run_id'] for r in new], ['C2610-0001', 'C2610-0002', 'C2610-0003', 'C2610-0004'])
        self.assertEqual(by['blog-1']['status'], 'completed')
        self.assertEqual(by['blog-1']['platform_group'], 'code')
        self.assertEqual(by['blog-1']['why_not_answer'], 'I picked Next.js over WordPress because it is fast.')
        self.assertIsNone(by['blog-1']['cost_usd'])  # plan runs have no API cost
        self.assertEqual(by['store-1']['platform'], 'WordPress')
        self.assertIsNone(by['store-1']['why_not_answer'])
        self.assertEqual(by['org-1']['status'], 'limit_reached')
        self.assertEqual(by['page-1']['status'], 'model_switched')
        self.assertTrue(by['page-1']['control'])
        # Exporting again adds nothing; the file holds one line per run.
        self.assertEqual(records.export('choose', '2026-10', [jobs / 'job-a']), [])
        self.assertEqual(len(records.read_records(defs.runs_file('choose', '2026-10'))), 4)

    def test_reruns_never_join_a_batch(self):
        jobs = Path(self.tmp.name) / 'jobs'
        job = trial(jobs, 'rerun-job', 'blog-1__a')
        manifest = json.loads((job / 'wpab-manifest.json').read_text())
        (job / 'wpab-manifest.json').write_text(json.dumps({**manifest, 'kind': 'rerun', 'batch': None, 'rerun_of': 'C2610-0001'}))
        self.assertEqual(records.export('choose', '2026-10', [job]), [])
        self.assertFalse(defs.runs_file('choose', '2026-10').exists())


class Stalled(unittest.TestCase):
    def test_stalled_run_counts_its_scaffold(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(defs, 'OUT', Path(tmp) / 'data'):
            jobs = Path(tmp) / 'jobs'
            job = trial(jobs, 'job-s', 'blog-1__s', platform='Nothing built')
            t = job / 'blog-1__s'
            result = json.loads((t / 'result.json').read_text())
            result['step_results'][0]['exception_info'] = {'exception_type': 'AgentTimeoutError', 'exception_message': 'timed out'}
            (t / 'result.json').write_text(json.dumps(result))
            (t / 'steps/request/agent/antigravity-stream.jsonl').write_text('{"tool_info": {"parameters": {"CommandLine": "npm create vite@latest . -- --template react"}}}\n')
            r = records.export('choose', '2026-10', [job])[0]
        self.assertEqual((r['status'], r['platform'], r['stalled']), ('completed', 'Plain HTML or React', True))


if __name__ == '__main__':
    unittest.main()


class SameModel(unittest.TestCase):
    def test_cursor_names(self):
        self.assertTrue(records._same_model('Grok 4.7', 'cursor/grok-4.7'))
        self.assertTrue(records._same_model('grok-4.7[effort=high]', 'cursor/grok-4.7'))
        self.assertFalse(records._same_model('gpt-5.6-sol-medium', 'cursor/grok-4.7'))
