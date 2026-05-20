from flask import Flask, request, jsonify

import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer, f1_score

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

    #-----------------------------------------------------
    # Tune Machine-Learning Model
    # ----------------------------------------------------

    # # 1. Initialize the model
    # iforest = IsolationForest()

    # # 2. Define the grid of parameters to search exhaustively
    # param_grid = {
    #     'n_estimators': [50, 100, 200],
    #     'max_samples': ['auto', 0.5, 1, 10, 100],
    #     'contamination': [0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5],
    #     'random_state': [42]
    # }

    # # 3. Setup GridSearchCV (Assuming you have y_train for scoring)
    # # If unsupervised, you must define a custom 'scoring' function

    # def scorer_f(estimator, X):   #your own scorer
    #     return np.mean(estimator.decision_function(X))
    #     #return np.mean(estimator.score_samples(X))

    # grid_search = GridSearchCV(
    #     estimator=iforest, 
    #     param_grid=param_grid, 
    #     scoring=scorer_f,
    #     cv=5, 
    #     n_jobs=-1
    # )

    # # 4. Fit the grid search
    # grid_search.fit(X.values)

    # # 5. Access the best parameters
    # print(f"Best Parameters: {grid_search.best_params_}", flush=True)
    
    # return jsonify({
    #     "regression": False,
    # })

    # ----------------------------------------------------
    # Train anomaly model
    # ----------------------------------------------------

    model = IsolationForest(
        n_estimators=100,
        max_samples='auto',
        contamination=0.2,
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

    print(f"current Metrics {current_vector}", flush=True)

    # ----------------------------------------------------
    # Predict anomaly
    # ----------------------------------------------------

    #print(f"Current vector for {route}:", current_vector, flush=True)

    prediction = model.predict(current_vector)[0]

    raw_scores = model.decision_function(current_vector)

    #prediction = model.predict(X.values)[0]

    #raw_scores = model.decision_function(X.values)

    # -----------------------------
    # Sort by most anomalous
    # -----------------------------

    # Sort indices in ascending order (most negative/anomalous first)
    sorted_indices = np.argsort(raw_scores)

    # Create a DataFrame to view the sorted scores alongside original data
    anomaly_results = pd.DataFrame({
        'Anomaly_Score': raw_scores[sorted_indices],
        'Original_Index': sorted_indices
    })


    # -----------------------------
    # Display results
    # -----------------------------
    
    # View the top 5 most anomalous points
    print(anomaly_results.head(50), flush=True)

    # To extract the actual anomalous rows from your original dataset:
    top_5_anomalies = X.iloc[sorted_indices[:5]]
    print(top_5_anomalies, flush=True)


    raw_score = raw_scores[0]

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

    return jsonify({

        "route": route,

        "regression": bool(regression),

        "anomaly_score": fmt(anomaly_score),

        "zscore": fmt(zscore),

        "confidence": fmt(confidence),

        "severity": severity(anomaly_score),

        "current": current,

        "baseline": baseline
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5200
    )
