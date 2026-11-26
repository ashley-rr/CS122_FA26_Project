import base64
import binascii
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from flask import Flask, Response, abort, jsonify, render_template

app = Flask(__name__)
GAMES_CSV = Path(__file__).resolve().parents[1] / "data" / "games.csv"
NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "data_analysis.ipynb"
PLOT_CELLS = {
    "opening-frequency": "6310283e",
    "win-rate": "9e1f2cc1",
    "opening-win-rates": "845f1cdb",
    "qq-original": "fa5598b6",
    "qq-transformed": "78949b24",
    "residuals": "e591cfdd",
    "game-length": "d69ae988",
}


def get_win_rates(csv_path):
    wins = {"white": 0, "black": 0}
    with csv_path.open(encoding="utf-8-sig", newline="") as games:
        rows = csv.DictReader(games)
        if "winner" not in (rows.fieldnames or []):
            raise ValueError("The games CSV must contain a winner column.")
        for row in rows:
            winner = row["winner"]
            if winner in wins:
                wins[winner] += 1

    total = sum(wins.values())
    return {
        "decisive_games": total,
        "sides": {
            side: {"wins": count, "rate": count / total * 100 if total else None}
            for side, count in wins.items()
        },
    }


def get_analysis(csv_path):
    openings = defaultdict(lambda: {"games": 0, "white": 0, "black": 0, "turns": 0})
    with csv_path.open(encoding="utf-8-sig", newline="") as games:
        rows = csv.DictReader(games)
        required = {"winner", "opening_family", "turns"}
        if not required.issubset(rows.fieldnames or []):
            raise ValueError("The games CSV must contain winner, opening_family, and turns columns.")
        for row in rows:
            opening = openings[row["opening_family"]]
            opening["games"] += 1
            opening["turns"] += int(row["turns"])
            if row["winner"] in ("white", "black"):
                opening[row["winner"]] += 1

    counts = Counter({name: data["games"] for name, data in openings.items()})
    popular = counts.most_common(10)
    rates = [
        {
            "name": name,
            "games": data["games"],
            "white": 100 * data["white"] / data["games"],
            "black": 100 * data["black"] / data["games"],
        }
        for name, data in openings.items()
        if data["games"] >= 100
    ]
    lengths = [
        {
            "name": name,
            "games": count,
            "mean": openings[name]["turns"] / count,
        }
        for name, count in counts.most_common()
        if name.lower() != "other"
    ][:10]
    return {
        "total_games": sum(counts.values()),
        "win_rates": get_win_rates(csv_path),
        "popular": popular,
        "opening_rates": sorted(rates, key=lambda row: row["games"], reverse=True),
        "lengths": lengths,
    }


@app.get("/")
def index():
    try:
        analysis = get_analysis(GAMES_CSV)
    except FileNotFoundError:
        return render_template("index.html", error="Could not find data/games.csv."), 503
    except ValueError as exc:
        app.logger.error("Invalid games CSV: %s", exc)
        return render_template("index.html", error="The games data is invalid. Check the server logs."), 503
    return render_template("index.html", analysis=analysis)


@app.get("/api/win-rates")
def win_rates():
    try:
        return jsonify(get_win_rates(GAMES_CSV))
    except FileNotFoundError:
        return jsonify(error="Could not find data/games.csv."), 503


@app.get("/notebook-plots/<plot_name>")
def notebook_plot(plot_name):
    if plot_name not in PLOT_CELLS:
        abort(404)
    try:
        with NOTEBOOK.open(encoding="utf-8") as notebook_file:
            notebook = json.load(notebook_file)
        cell = next(
            (cell for cell in notebook["cells"] if cell.get("id") == PLOT_CELLS[plot_name]),
            None,
        )
        if cell is None:
            raise ValueError(f"Notebook cell {PLOT_CELLS[plot_name]} was not found.")
        image = next(
            (
                output["data"]["image/png"]
                for output in cell.get("outputs", [])
                if "image/png" in output.get("data", {})
            ),
            None,
        )
        if image is None:
            raise ValueError("The notebook cell has no saved PNG output.")
        if isinstance(image, list):
            image = "".join(image)
        return Response(base64.b64decode(image, validate=True), mimetype="image/png")
    except (OSError, ValueError, KeyError, TypeError, binascii.Error) as exc:
        app.logger.error("Notebook plot %s is unavailable: %s", plot_name, exc)
        return Response("Notebook plot unavailable. Check the server logs.", status=503, mimetype="text/plain")