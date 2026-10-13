"""Building the site's data: the current month, and earlier months kept for links into them."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from wpab import defs, site


class EarlierMonths(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / 'data' / 'choose' / 'runs').mkdir(parents=True)
        for b in ('2026-09', '2026-10', '2026-11'):
            (root / 'data' / 'choose' / 'runs' / f'{b}.jsonl').write_text('')
        self.out = root / 'site-data'
        patches = [mock.patch.object(defs, 'OUT', root / 'data'), mock.patch.object(defs, 'SITE_DATA', self.out),
                   mock.patch.object(site, 'choose', side_effect=lambda b: {'batch': {'id': b}})]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_earlier_months_written_once(self):
        site.build('choose', '2026-10')
        self.assertTrue((self.out / 'choose.js').exists())
        self.assertIn('"2026-09"', (self.out / 'choose-2026-09.js').read_text())
        self.assertFalse((self.out / 'choose-2026-10.js').exists())
        (self.out / 'choose-2026-09.js').write_text('kept')
        site.build('choose', '2026-11')
        self.assertEqual((self.out / 'choose-2026-09.js').read_text(), 'kept')
        self.assertIn('"2026-10"', (self.out / 'choose-2026-10.js').read_text())
        self.assertIn('"2026-11"', (self.out / 'choose.js').read_text())


if __name__ == '__main__':
    unittest.main()
