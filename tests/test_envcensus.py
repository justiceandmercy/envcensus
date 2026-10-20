import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import envcensus


class EnvCensusTests(unittest.TestCase):
    def test_finds_missing_variable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text('import os\nvalue = os.getenv("API_TOKEN")\n')
            (root / ".env.example").write_text("DATABASE_URL=\n")
            references = envcensus.scan_references(root)
            self.assertEqual(references, {"API_TOKEN": ["app.py:2"]})
            report = envcensus.build_report(root, references, {}, {"DATABASE_URL": ""})
            self.assertEqual(report["missing_from_example"], ["API_TOKEN"])
            self.assertEqual(report["unused_in_example"], ["DATABASE_URL"])

    def test_parses_env_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("FOO=bar\n# comment\nBAR=\n")
            self.assertEqual(set(envcensus.parse_env_file(root / ".env")), {"FOO", "BAR"})


if __name__ == "__main__":
    unittest.main()
