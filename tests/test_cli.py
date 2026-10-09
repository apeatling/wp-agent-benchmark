"""Signing in, local versus published data, and classifying without a TypeSafe key."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from wpab import classify, cli, defs

OPUS, GROK = defs.agents()['opus-5-5-claude-code'], defs.agents()['grok-4-7-grok-build']


class SignIn(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.patches = [mock.patch.dict('os.environ', {}, clear=True), mock.patch.object(cli.Path, 'home', return_value=Path(self.home.name))]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.home.cleanup()

    def test_api_key_wins_then_plan_then_nothing(self):
        self.assertIsNone(cli.sign_in(OPUS))
        cli.os.environ['CLAUDE_CODE_OAUTH_TOKEN'] = 'x'
        self.assertEqual(cli.sign_in(OPUS), 'plan')
        cli.os.environ['ANTHROPIC_API_KEY'] = 'x'
        self.assertEqual(cli.sign_in(OPUS), 'api')

    def test_open_models_use_openrouter(self):
        self.assertEqual(cli.api_key(GROK), 'OPENROUTER_API_KEY')
        self.assertEqual(cli.api_key(defs.agents()['kimi-k3-kimi-code']), 'OPENROUTER_API_KEY')
        self.assertIn('OPENROUTER_API_KEY', cli.sign_in_help(GROK))
        self.assertIn('claude setup-token', cli.sign_in_help(OPUS))

    def test_pick_agents_explains_what_is_missing(self):
        with self.assertRaises(SystemExit) as e:
            cli.pick_agents('grok-4-7-grok-build')
        self.assertIn('OPENROUTER_API_KEY', str(e.exception))
        cli.os.environ['OPENROUTER_API_KEY'] = 'x'
        self.assertEqual(cli.pick_agents('grok-4-7-grok-build'), [(GROK, 'api')])
        self.assertEqual(cli.pick_agents('opus-5-5-claude-code:plan'), [(OPUS, 'plan')])


class LocalData(unittest.TestCase):
    def test_local_unless_published(self):
        with mock.patch.object(defs, 'OUT', defs.DATA), mock.patch.object(defs, 'SITE_DATA', defs.ROOT / 'site' / 'data'):
            self.assertFalse(defs.local())
            defs.use_local()
            self.assertTrue(defs.local())
            self.assertEqual(defs.runs_file('choose', '2026-10'), defs.ROOT / 'data' / 'local' / 'choose' / 'runs' / '2026-10.jsonl')
            self.assertEqual(defs.SITE_DATA, defs.ROOT / 'site' / 'data-local')

    def test_choose_word_is_optional(self):
        for argv in (['wpab', 'status', 'choose'], ['wpab', 'status']):
            with mock.patch.object(cli.sys, 'argv', argv), mock.patch.object(cli, 'status_lines', return_value=[]) as status, \
                    mock.patch.object(cli.defs, 'use_local'), self.assertRaises(SystemExit):
                cli.main()
            self.assertEqual(status.call_args[0][0].benchmark, 'choose')


class LocalRunIds(unittest.TestCase):
    def test_local_runs_are_marked(self):
        from test_records import trial
        from wpab import records
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(defs, 'OUT', Path(tmp) / 'data'), \
                mock.patch.object(defs, 'LOCAL_OUT', Path(tmp) / 'data'):
            new = records.export('choose', '2026-10', [trial(Path(tmp) / 'jobs', 'job-a', 'blog-1__a')])
        self.assertEqual(new[0]['run_id'], 'C2610-L0001')


class ClaudeFallback(unittest.TestCase):
    def test_answers_come_back_in_jevs_shape(self):
        questions = {'platform': classify.choice_q('What it built with.', {'Astro': '...', 'WordPress': '...'}),
                     'considered_wordpress': {'type': 'noul', 'instructions': 'It mentioned WordPress.'}}
        reply = {'platform': {'choice': 'Hugo', 'confidence': 0.9}, 'considered_wordpress': {'noul': 1.4}}
        with mock.patch.dict('os.environ', {}, clear=True), mock.patch('wpab.review.run_reviewer', return_value=reply):
            model, answers = classify.ask('state', questions)
        self.assertEqual(model, 'claude-haiku-5-5')
        self.assertEqual(answers['platform']['confidence'], 0.0)  # not an option, so it goes to review
        self.assertEqual(answers['considered_wordpress']['noul'], 1.0)


if __name__ == '__main__':
    unittest.main()


class OwnPrompt(unittest.TestCase):
    """`wpab try --prompt`: a one-off task built like the published ones, kept out of tasks/."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = mock.patch.object(cli, 'CUSTOM_TASKS', Path(self.tmp.name))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_builds_a_task_in_the_agents_sandbox(self):
        brief = 'We are building an official website for our municipality, managed by 20 to 30 staff.'
        req, folder = cli.own_prompt(brief, GROK)
        self.assertTrue(req['id'].startswith('own-'))
        self.assertEqual(folder, Path(self.tmp.name) / GROK['environment'])
        task = folder / req['id']
        self.assertEqual((task / 'steps' / 'request' / 'instruction.md').read_text(), brief + '\n')
        self.assertIn('kind = "own"', (task / 'task.toml').read_text())
        self.assertTrue((task / 'environment' / 'Dockerfile').exists())
        # The same prompt reuses its task.
        self.assertEqual(cli.own_prompt(brief, GROK), (req, folder))
