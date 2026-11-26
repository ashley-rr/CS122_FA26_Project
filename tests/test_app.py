import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gui.app import PLOT_CELLS, app, get_analysis


class AnalysisTests(unittest.TestCase):
    def test_analysis_uses_correct_denominators_and_filters(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "games.csv"
            with path.open("w", encoding="utf-8", newline="") as games:
                writer = csv.writer(games)
                writer.writerow(["winner", "opening_family", "turns"])
                writer.writerows([["white", "Opening A", 20]] * 60)
                writer.writerows([["black", "Opening A", 40]] * 30)
                writer.writerows([["draw", "Opening A", 60]] * 10)
                writer.writerow(["white", "Other", 10])

            analysis = get_analysis(path)

        self.assertEqual(analysis["total_games"], 101)
        self.assertEqual(analysis["win_rates"]["decisive_games"], 91)
        self.assertEqual(analysis["opening_rates"], [
            {"name": "Opening A", "games": 100, "white": 60.0, "black": 30.0}
        ])
        self.assertEqual(analysis["lengths"], [
            {"name": "Opening A", "games": 100, "mean": 30.0}
        ])

    def test_page_and_existing_api_use_same_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "games.csv"
            path.write_text(
                "winner,opening_family,turns\n"
                "white,Test Opening,20\nwhite,Test Opening,30\n"
                "black,Test Opening,40\ndraw,Test Opening,50\n",
                encoding="utf-8",
            )
            with patch("gui.app.GAMES_CSV", path):
                client = app.test_client()
                response = client.get("/")
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"66.67%", response.data)
                self.assertIn(b"Test Opening", response.data)
                self.assertEqual(client.get("/api/win-rates").json["decisive_games"], 3)

    def test_missing_data_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("gui.app.GAMES_CSV", Path(directory) / "missing.csv"):
                client = app.test_client()
                self.assertEqual(client.get("/").status_code, 503)
                self.assertEqual(client.get("/api/win-rates").status_code, 503)
                self.assertIn(b"Could not find data/games.csv", client.get("/").data)

    def test_notebook_plots_serve_saved_cell_images(self):
        notebook = {
            "cells": [
                {"id": cell_id, "outputs": [{"data": {"image/png": "cGxvdA=="}}]}
                for cell_id in PLOT_CELLS.values()
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "analysis.ipynb"
            path.write_text(json.dumps(notebook), encoding="utf-8")
            with patch("gui.app.NOTEBOOK", path):
                client = app.test_client()
                for name in PLOT_CELLS:
                    with self.subTest(plot=name):
                        response = client.get(f"/notebook-plots/{name}")
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.mimetype, "image/png")
                        self.assertEqual(response.data, b"plot")
                self.assertEqual(client.get("/notebook-plots/unknown").status_code, 404)

    def test_missing_notebook_plot_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "analysis.ipynb"
            path.write_text('{"cells": []}', encoding="utf-8")
            with patch("gui.app.NOTEBOOK", path):
                response = app.test_client().get("/notebook-plots/qq-original")
                self.assertEqual(response.status_code, 503)
                self.assertIn(b"Notebook plot unavailable", response.data)


if __name__ == "__main__":
    unittest.main()
