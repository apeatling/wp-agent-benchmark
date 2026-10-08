"""Classifying runs: answers land in the right fields, and doubtful ones are marked for review. Jev is mocked."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from wpab import classify, defs, records
from test_records import trial


def fake_ask(state, questions):
    answers = {}
    for name, q in questions.items():
        if name == 'platform':
            answers[name] = {'type': 'choice', 'choice': 'Next.js', 'confidence': 0.92}
        elif q['type'] == 'choice':
            answers[name] = {'type': 'choice', 'choice': 'overkill', 'confidence': 0.81}
        else:
            sure = {'considered_wordpress', 'pattern:one-command', 'deciding:overkill', 'asked:overkill', 'asked:upkeep'}
            answers[name] = {'type': 'noul', 'noul': {'asked:upkeep': 0.8}.get(name, 1.0 if name in sure else 0.0)}
    return 'jev-1.13.0', answers


class Classify(unittest.TestCase):
    def test_classify(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(defs, 'OUT', Path(tmp) / 'data'), mock.patch.object(defs, 'JOBS', Path(tmp) / 'jobs'), \
                mock.patch.object(classify, 'ask', side_effect=fake_ask), mock.patch.dict('os.environ', {'TYPESAFE_API_KEY': 'x'}):
            trial(defs.JOBS, 'job-a', 'blog-1__a')
            trial(defs.JOBS, 'job-a', 'store-1__b', request='store-1', platform='WordPress')
            trial(defs.JOBS, 'job-a', 'org-1__c', request='org-1', answer="I'm still setting up the project.")
            records.export('choose', '2026-10', [defs.JOBS / 'job-a'])
            classify.classify('choose', '2026-10')
            by = {r['request_id']: r for r in records.read_records(defs.runs_file('choose', '2026-10'))}
        blog, store = by['blog-1'], by['store-1']
        self.assertTrue(blog['considered_wordpress'])
        self.assertEqual(blog['reason_deciding'], 'overkill')
        self.assertEqual(blog['reason_asked'], 'overkill')
        self.assertEqual(blog['reasons_asked'], ['overkill', 'upkeep'])  # several reasons, strongest first
        self.assertEqual(blog['patterns'], ['one-command'])
        self.assertTrue(blog['detection']['agrees'])
        self.assertEqual(blog['classifier']['model'], 'jev-1.13.0')
        self.assertFalse(blog['classifier']['needs_review'])
        # It chose WordPress, but Jev read Next.js: a person checks it.
        self.assertFalse(store['detection']['agrees'])
        self.assertTrue(store['classifier']['needs_review'])
        self.assertIsNone(store['reason_deciding'])
        # An answer that doesn't mention WordPress gives no reason.
        self.assertIsNone(by['org-1']['reason_asked'])


class FirstReply(unittest.TestCase):
    def test_stops_at_the_nudge(self):
        import tempfile, json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            agent = Path(d) / 'steps' / 'request' / 'agent'
            agent.mkdir(parents=True)
            (agent / 'trajectory.json').write_text(json.dumps({'steps': [
                {'source': 'user', 'message': 'Build a site'},
                {'source': 'agent', 'message': 'WordPress or custom code?'},
                {'source': 'user', 'message': 'Use your best judgement and go ahead.'},
                {'source': 'agent', 'message': 'Built it in Astro.'}]}))
            self.assertEqual(classify.first_reply(Path(d)), 'WordPress or custom code?')


class Review(unittest.TestCase):
    def test_reviewer_settles_flags_and_never_reviews_its_own_maker(self):
        from wpab import review
        self.assertEqual(review.reviewer('anthropic/claude-opus-5-5'), review.GPT)
        self.assertEqual(review.reviewer('openai/gpt-6.1-sol'), review.OPUS)
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(defs, 'OUT', Path(tmp) / 'data'), mock.patch.object(defs, 'JOBS', Path(tmp) / 'jobs'), \
                mock.patch.object(classify, 'ask', side_effect=fake_ask), mock.patch.dict('os.environ', {'TYPESAFE_API_KEY': 'x'}):
            trial(defs.JOBS, 'job-a', 'store-1__b', request='store-1', platform='WordPress')
            records.export('choose', '2026-10', [defs.JOBS / 'job-a'])
            classify.classify('choose', '2026-10')
            got = {'platform': 'WordPress', 'notes': 'The files are a WordPress theme.'}
            with mock.patch.object(review, 'run_reviewer', return_value=got):
                done = review.review('choose', '2026-10')
            r = records.read_records(defs.runs_file('choose', '2026-10'))[0]
        self.assertEqual(len(done), 1)
        self.assertFalse(r['classifier']['needs_review'])
        self.assertEqual(r['classifier']['review']['changed'], {})  # the detector was right
        self.assertEqual(r['platform'], 'WordPress')


if __name__ == '__main__':
    unittest.main()
