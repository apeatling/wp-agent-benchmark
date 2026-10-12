"""Reading the hidden answers line of each recommendation in advice.md, and the reach it gives."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from wpab import deep

GROUPED = {'n': 4,
           'claims': [{'id': 'slow-without-caching', 'runs': ['r1', 'r2']}, {'id': 'migration-means-rebuild', 'runs': ['r3']}],
           'conditions': [{'id': 'needs-blog', 'runs': ['r4']}]}
RUNS = [{'run_id': 'r1', 'patterns': []}, {'run_id': 'r2', 'patterns': ['didnt-ask']},
        {'run_id': 'r3', 'patterns': ['didnt-ask']}, {'run_id': 'r4', 'patterns': ['editable-html']}]


def advice(answers):
    return f"""# Advice

An opening paragraph.

## Make caching the default

<!-- answers: {answers} -->
A lead sentence.

**Impact:** high
**Kind:** update

**Evidence:**
- Agents said it.
"""


class Answers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / 'grouped.json').write_text(json.dumps(GROUPED))
        (self.dir / 'runs.json').write_text(json.dumps(RUNS))
        patcher = mock.patch.object(deep, 'folder', return_value=self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def idea(self, answers):
        (self.dir / 'advice.md').write_text(advice(answers))
        return next(s for s in deep.sections('2026-10')['sections'] if s.get('recommendation'))

    def test_all_filled(self):
        sec = self.idea('reasons=upkeep,default claims=slow-without-caching patterns=editable-html')
        self.assertEqual(sec['answers'], {'reasons': ['upkeep', 'default'], 'claims': ['slow-without-caching'], 'patterns': ['editable-html']})
        self.assertEqual(sec['reasons'], ['upkeep', 'default'])
        self.assertEqual(sec['reach']['sites'], 3)

    def test_empty_claims_keeps_next_key(self):
        sec = self.idea('reasons=default claims= patterns=didnt-ask')
        self.assertEqual(sec['answers'], {'reasons': ['default'], 'claims': [], 'patterns': ['didnt-ask']})
        self.assertEqual(sec['reach']['sites'], 2)
        self.assertEqual(sec['reach']['unknown_ids'], [])

    def test_empty_reasons_keeps_claims(self):
        sec = self.idea('reasons= claims=slow-without-caching,migration-means-rebuild patterns=editable-html')
        self.assertEqual(sec['answers'], {'reasons': [], 'claims': ['slow-without-caching', 'migration-means-rebuild'], 'patterns': ['editable-html']})
        self.assertEqual(sec['reasons'], [])
        self.assertEqual(sec['reach']['sites'], 4)

    def test_empty_last_value(self):
        sec = self.idea('reasons=upkeep claims=slow-without-caching patterns=')
        self.assertEqual(sec['answers'], {'reasons': ['upkeep'], 'claims': ['slow-without-caching'], 'patterns': []})
        self.assertEqual(sec['reach']['sites'], 2)

    def test_several_empty_values(self):
        sec = self.idea('reasons= claims=slow-without-caching patterns=')
        self.assertEqual(sec['answers'], {'reasons': [], 'claims': ['slow-without-caching'], 'patterns': []})
        self.assertEqual(sec['reach']['sites'], 2)

    def test_space_after_equals_still_read(self):
        sec = self.idea('reasons= default claims= slow-without-caching patterns= didnt-ask')
        self.assertEqual(sec['answers'], {'reasons': ['default'], 'claims': ['slow-without-caching'], 'patterns': ['didnt-ask']})


if __name__ == '__main__':
    unittest.main()
