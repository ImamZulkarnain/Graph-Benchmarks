"""Small temporary files shared by the tests."""

import tempfile
import unittest
from pathlib import Path


class FileTestCase(unittest.TestCase):
    def setUp(self):
        folder = Path(__file__).resolve().parents[1] / "tmp"
        folder.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="unit_test_", dir=folder)
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)

    def write_graph(self, body="4 4 4\n1 2\n2 3\n3 1\n3 4\n"):
        path = self.folder / "graph.mtx"
        path.write_text("%%MatrixMarket matrix coordinate pattern symmetric\n" + body,
                        encoding="utf-8")
        return path
