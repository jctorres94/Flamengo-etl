from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class FlamengoAppSmokeTest(unittest.TestCase):
    def test_app_starts_and_renders(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path), default_timeout=60).run()
        self.assertEqual(len(app.exception), 0, app.exception)
        self.assertGreaterEqual(len(app.metric), 10)
        self.assertGreaterEqual(len(app.get("plotly_chart")), 1)
        self.assertGreaterEqual(len(app.dataframe), 1)
        self.assertIn("Mercado", [tab.label for tab in app.tabs])
        movement_filter = next(radio for radio in app.radio if radio.label == "Movimento")
        self.assertEqual(movement_filter.options, ["Todos", "Compras", "Vendas"])


if __name__ == "__main__":
    unittest.main()
