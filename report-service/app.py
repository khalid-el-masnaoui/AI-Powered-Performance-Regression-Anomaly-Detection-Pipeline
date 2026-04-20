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


# ---------------------------------------------------
# Save Regression History
# ---------------------------------------------------
def save_regression_history(route, payload):

    safe_route = route.replace("/", "_")

    path = os.path.join(
        REGRESSION_HISTORY_DIR,
        f"{safe_route}.json"
    )

    history = []

    if os.path.exists(path):
        with open(path, "r") as f:
            history = json.load(f)

    history.append(payload)

    with open(path, "w") as f:
        json.dump(history, f, indent=2)

    return history

# ---------------------------------------------------
# Generate Regression Trend Chart
# ---------------------------------------------------
def generate_regression_chart(route, history, metric):

    timestamps = [
    h["timestamp"]
    for h in history
    ]

    values = [
        h["current"].get(metric, 0)
        for h in history
    ]

    plt.figure(figsize=(10, 4))

    plt.plot(timestamps, values)

    plt.xticks(rotation=45)

    plt.title(f"{route} - {metric} Trend")

    plt.tight_layout()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"{route.replace('/', '_')}_{metric}_{timestamp}.png"

    chart_path = os.path.join(
        REGRESSION_CHART_DIR,
        f"{filename}"
    )
    plt.savefig(chart_path)

    plt.close()

    return chart_path

# ---------------------------------------------------
# Generate Baseline PDF
# ---------------------------------------------------
@app.route("/generate-baseline", methods=["POST"])
def generate_baseline():

    data = request.json

    route = data.get("route")
    p95 = float(data.get("p95"))
    p99 = float(data.get("p99", 0))
    avg = float(data.get("avg", 0))
    error_rate = float(data.get("error_rate", 0))
    max_latency = float(data.get("max_latency", 0))
    throughput = float(data.get("throughput", 0))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    safe_route = route.replace("/", "_")

    filename = f"{safe_route}_{timestamp}.pdf"

    filepath = os.path.join(BASELINE_DIR, filename)

    # ---------------------------------------------
    # Save historical trend
    # ---------------------------------------------
    history = save_history(route, {
        "p95": p95,
        "p99": p99,
        "avg": avg,
        "error_rate": error_rate,
        "max_latency": max_latency,
        "throughput": throughput
    })

    # ---------------------------------------------
    # Generate chart
    # ---------------------------------------------
    chart_path = generate_chart(route, history)

    # ---------------------------------------------
    # PDF
    # ---------------------------------------------
    doc = SimpleDocTemplate(filepath, pagesize=A3)

    styles = getSampleStyleSheet()

    elements = []
