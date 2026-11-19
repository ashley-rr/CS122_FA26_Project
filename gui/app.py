import csv
from pathlib import Path

from flask import Flask, jsonify, render_template

app = Flask(__name__)
GAMES_CSV = Path(__file__).resolve().parents[1] / "notebooks" / "games.csv"


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


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/win-rates")
def win_rates():
    try:
        return jsonify(get_win_rates(GAMES_CSV))
    except FileNotFoundError:
        return jsonify(error="Could not find notebooks/games.csv."), 503