from flask import Flask, request, jsonify

import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest

app = Flask(__name__)

# --------------------------------------------------------
# Helpers
# --------------------------------------------------------

def fmt(v):

    try:
        return round(float(v), 4)
    except:
        return 0


def severity(score):

    if score > 0.9:
        return "CRITICAL"

    if score > 0.75:
        return "HIGH"

    if score > 0.5:
        return "MEDIUM"

    return "LOW"


# --------------------------------------------------------
# AI Regression Anomaly Detection
# --------------------------------------------------------

@app.route("/detect", methods=["POST"])
def detect():

    data = request.json

    route = data["route"]

    history = data["history"]

    current = data["current"]

    baseline = data["baseline"]

    # ----------------------------------------------------
    # Need enough history
    # ----------------------------------------------------

    if len(history) < 10:

        print(f"Not enough history for {route}", flush=True)

        return jsonify({
            "status": "not-enough-history",
            "anomaly_score": 0,
            "regression": False
        })

    print(f"Received data for {route} - history length: {len(history)}", flush=True)
    
    # ----------------------------------------------------
    # Historical dataframe
    # ----------------------------------------------------

    #print(f"History for {route}:", history, flush=True)
    
    df = pd.DataFrame(history)

    features = [
        "p95",
        "p99",
        "avg",
        "throughput",
        #"error_rate",
        "max_latency"
    ]

    X = df[features]

    #print(f"Feature data for {route}:", X, flush=True)

    # ----------------------------------------------------
    # Train anomaly model
    # ----------------------------------------------------

    model = IsolationForest(
        contamination=0.1,
        random_state=42
    )
