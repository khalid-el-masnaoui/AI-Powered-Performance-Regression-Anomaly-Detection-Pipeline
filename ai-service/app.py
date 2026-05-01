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

    model.fit(X.values)

    # ----------------------------------------------------
    # Current observation
    # ----------------------------------------------------

    current_vector = [[

        current.get("p95", 0),

        current.get("p99", 0),

        current.get("avg", 0),

        current.get("throughput", 0),

        #current.get("error_rate", 0),

        current.get("max_latency", 0)

    ]]

    # ----------------------------------------------------
    # Predict anomaly
    # ----------------------------------------------------

    #print(f"Current vector for {route}:", current_vector, flush=True)

    prediction = model.predict(current_vector)[0]

    raw_score = model.decision_function(current_vector)[0]

    # normalize
    anomaly_score = min(
        1,
        max(
            0,
            abs(raw_score)
        )
    )

    regression = prediction == -1

    print(f"Raw anomaly score for {route}: {raw_score}", flush=True)
    print(f"prediction for {route}: {prediction}", flush=True)
    print(f"Anomaly detection for {route} - score: {anomaly_score}, regression: {regression}", flush=True)

    # ----------------------------------------------------
    # Additional z-score
    # ----------------------------------------------------

    p95_mean = df["p95"].mean()

    p95_std = df["p95"].std()

    if p95_std == 0:
        zscore = 0
    else:
        zscore = (
            current["p95"] - p95_mean
        ) / p95_std

    # ----------------------------------------------------
    # Confidence
    # ----------------------------------------------------

    confidence = min(
        1,
        abs(zscore) / 5
    )
