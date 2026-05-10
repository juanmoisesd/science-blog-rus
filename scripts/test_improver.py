import unittest
from scripts.improve_teaching_guides import TeachingGuideImprover
import os
import shutil

class TestTeachingGuideImprover(unittest.TestCase):
    def setUp(self):
        # We don't need a real key for these unit tests if we don't call fetch_records
        self.improver = TeachingGuideImprover(None)
        self.test_dir = "test_output"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_slugify(self):
        record = {
            "metadata": {"title": "Teaching Guide (Русский): Биомаркеры Neuroinflamacion"},
            "doi": "10.1234/test"
        }
        self.improver.improve_record(record, self.test_dir)
        # python-slugify should handle Cyrillic by transliterating or keeping if configured,
        # default transliterates: biomarkery-neuroinflamacion
        expected_slug = "teaching-guide-russkii-biomarkery-neuroinflamacion"
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, expected_slug)))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, expected_slug, "teaching_guide_extended.md")))

    def test_context_generation(self):
        context_sleep = self.improver._get_context("sleep quality")
        self.assertIn("sleep quality", context_sleep)

        context_generic = self.improver._get_context("unknown topic")
        self.assertIn("unknown topic", context_generic)

if __name__ == "__main__":
    unittest.main()
