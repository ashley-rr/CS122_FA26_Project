import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gui.app import PLOT_CELLS, app, get_analysis, get_csv_preview


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

    def test_page_displays_analysis_and_conclusion(self):
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
                self.assertIn(b"Future Work", response.data)
                self.assertIn(b'href="/dataset"', response.data)
                self.assertNotIn(b'id="dataset"', response.data)
                self.assertGreater(
                    response.data.index(b'id="conclusion"'),
                    response.data.index(b'id="length"'),
                )
                self.assertEqual(client.get("/api/win-rates").status_code, 404)

    def test_csv_previews_select_rows_and_handle_small_datasets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "games.csv"
            with path.open("w", encoding="utf-8", newline="") as games:
                writer = csv.writer(games)
                writer.writerow(["id"])
                writer.writerows([[str(index)] for index in range(20)])

            first = get_csv_preview(path, "first")
            last = get_csv_preview(path, "last")
            self.assertEqual(first["columns"], ["id"])
            self.assertEqual(first["rows"], [[str(index)] for index in range(10)])
            self.assertEqual(last["rows"], [[str(index)] for index in range(10, 20)])
            for count in (5, 10, 15):
                with self.subTest(count=count):
                    rows = get_csv_preview(path, f"random-{count}")["rows"]
                    self.assertEqual(len(rows), count)
                    self.assertEqual(len({row[0] for row in rows}), count)
                    self.assertTrue(all(0 <= int(row[0]) < 20 for row in rows))

            path.write_text("id\none\ntwo\n", encoding="utf-8")
            self.assertEqual(len(get_csv_preview(path, "random-15")["rows"]), 2)
            path.write_text("id\n", encoding="utf-8")
            self.assertEqual(get_csv_preview(path, "last")["rows"], [])

    def test_preview_buttons_render_requested_sample_and_escape_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "games.csv"
            with path.open("w", encoding="utf-8", newline="") as games:
                writer = csv.writer(games)
                writer.writerow(["winner", "opening_family", "turns", "id"])
                writer.writerows([["white", "<opening>", 20, index] for index in range(20)])
            with patch("gui.app.GAMES_CSV", path):
                client = app.test_client()
                for selection, count in (("first", 10), ("last", 10), ("random-5", 5),
                                         ("random-10", 10), ("random-15", 15)):
                    with self.subTest(selection=selection):
                        response = client.get("/dataset", query_string={"preview": selection})
                        self.assertEqual(response.status_code, 200)
                        self.assertIn(f"Showing {count} rows:".encode(), response.data)
                        self.assertIn(b"&lt;opening&gt;", response.data)
                        self.assertIn(b'action="/dataset"', response.data)
                        self.assertIn(b'data-preview-url="/dataset/preview"', response.data)
                        self.assertIn(
                            f'value="{selection}" class="selected"'.encode(),
                            response.data,
                        )
                response = client.get("/dataset")
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Showing 10 rows: First 10 rows", response.data)
                self.assertIn(b'href="/"', response.data)
                self.assertEqual(client.get("/dataset?preview=invalid").status_code, 400)
                self.assertEqual(client.get("/dataset/preview?preview=invalid").status_code, 400)

                response = client.get("/dataset/preview?preview=random-5")
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Showing 5 rows: Random 5 rows", response.data)
                self.assertIn(b"&lt;opening&gt;", response.data)

    def test_missing_data_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("gui.app.GAMES_CSV", Path(directory) / "missing.csv"):
                client = app.test_client()
                self.assertEqual(client.get("/").status_code, 503)
                self.assertIn(b"Could not find data/games.csv", client.get("/").data)
                response = client.get("/dataset")
                self.assertEqual(response.status_code, 503)
                self.assertIn(b"Could not find data/games.csv", response.data)
                response = client.get("/dataset/preview")
                self.assertEqual(response.status_code, 503)
                self.assertIn(b"Could not find data/games.csv", response.data)

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
