import math
import os
import json
import time
import requests
import redis
from flask import Flask, request, jsonify

app = Flask(__name__)

# config (use env vars in real setup)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
AI_ANOMALY_DETECTION_URL = os.getenv("AI_ANOMALY_DETECTION_URL", "http://ai-service:5200")
REPORT_URL = os.getenv("REPORT_URL", "http://report-service:5000")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

print ("App started")

# -------------------------
# Prometheus query
# -------------------------
def query_prometheus_p95(route):
    query = f'''
    histogram_quantile(0.95,
      sum(rate(app_request_duration_seconds_bucket{{route="{route}"}}[2m])) by (le)
    )
    '''

    try:
        res = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
        data = res.json()

        results = data.get("data", {}).get("result", [])

        if not results: 
            return 0

        value = results[0]["value"][1]

        if value in ["NaN", "null", None]:
            return 0

        return round(float(value), 4)

    except Exception as e:
        print("Prometheus query error:", e)
        return 0
