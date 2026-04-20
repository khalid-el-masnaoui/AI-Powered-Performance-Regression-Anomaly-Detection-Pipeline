from flask import Flask, request, jsonify
from reportlab.platypus import (
    PageBreak,
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter, A3
import os
import datetime
import json

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

app = Flask(__name__)

BASELINES_BASE_DIR = "/reports/baselines"
REGRESSIONS_BASE_DIR = "/reports/regressions"

#baselines
BASELINE_DIR = f"{BASELINES_BASE_DIR}/baselines"
BASELINE_HISTORY_DIR = f"{BASELINES_BASE_DIR}/history"
BASELINE_CHART_DIR = f"{BASELINES_BASE_DIR}/charts"

#regressions
REGRESSIONS_DIR = f"{REGRESSIONS_BASE_DIR}/regressions"
REGRESSION_HISTORY_DIR = f"{REGRESSIONS_BASE_DIR}/history"
REGRESSION_CHART_DIR = f"{REGRESSIONS_BASE_DIR}/charts"


os.makedirs(BASELINE_DIR, exist_ok=True)
os.makedirs(BASELINE_HISTORY_DIR, exist_ok=True)
os.makedirs(BASELINE_CHART_DIR, exist_ok=True)


os.makedirs(REGRESSIONS_DIR, exist_ok=True)
os.makedirs(REGRESSION_HISTORY_DIR, exist_ok=True)
os.makedirs(REGRESSION_CHART_DIR, exist_ok=True)

# ---------------------------------------------------
# Format Numbers
# ---------------------------------------------------
def fmt(value):

    try:
        return f"{float(value):.4f}"
    except:
        return "0.0000"

# ---------------------------------------------------
# Format Latency in ms
# ---------------------------------------------------
def fmt_ms(value):
    return f"{float(value)*1000:.2f} ms"

# ---------------------------------------------------
# Save Baseline History
# ---------------------------------------------------
def save_history(route, metrics):

    safe_route = route.replace("/", "_")

    history_file = os.path.join(
        BASELINE_HISTORY_DIR,
        f"{safe_route}.json"
    )

    history = []

    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)

    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "p95": metrics["p95"],
        "p99": metrics["p99"],
        "avg": metrics["avg"],
        "error_rate": metrics["error_rate"],
        "max_latency": metrics["max_latency"],
        "throughput": metrics["throughput"]
    })

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    return history


# ---------------------------------------------------
# Generate Baseline Trend Chart
# ---------------------------------------------------
def generate_chart(route, history):

    df = pd.DataFrame(history)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"{route.replace('/', '_')}_{timestamp}.png"

    chart_path = os.path.join(
        BASELINE_CHART_DIR,
        f"{filename}"
    )

    plt.figure(figsize=(10, 5))

    plt.plot(df["timestamp"], df["p95"], marker="o")

    plt.title(f"P95 Trend — {route}")

    plt.xlabel("Time")
    plt.ylabel("Latency (seconds)")

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(chart_path)

    plt.close()

    return chart_path
