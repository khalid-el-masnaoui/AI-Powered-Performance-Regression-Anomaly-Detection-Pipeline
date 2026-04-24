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

def query_prometheus_metrics(route):
    # --------------------------------------------------
    # Helper
    # --------------------------------------------------

    def run_query(query):

        try:

            response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})

            data = response.json()

            results = data.get("data", {}).get("result", [])

            if not results:
                return 0

            value = results[0]["value"][1]

            if value in ["NaN", "null", None]:
                return 0

            return round(float(value), 4)

        except Exception as e:

            print(f"Prometheus query failed: {e}")

            return 0

    # --------------------------------------------------
    # P95
    # --------------------------------------------------

    p95_query = f'''
    histogram_quantile(
      0.95,
      sum(
        rate(
          app_request_duration_seconds_bucket{{route="{route}"}}[2m]
        )
      ) by (le)
    )
    '''

    # --------------------------------------------------
    # P99
    # --------------------------------------------------

    p99_query = f'''
    histogram_quantile(
      0.99,
      sum(
        rate(
          app_request_duration_seconds_bucket{{route="{route}"}}[2m]
        )
      ) by (le)
    )
    '''

    # --------------------------------------------------
    # AVG
    # --------------------------------------------------

    avg_query = f'''
    rate(
      app_request_duration_seconds_sum{{route="{route}"}}[2m]
    )
    /
    rate(
      app_request_duration_seconds_count{{route="{route}"}}[2m]
    )
    '''

    # --------------------------------------------------
    # ERROR RATE
    # --------------------------------------------------

    error_query = f'''
    (
      sum(
        rate(
          app_requests_total{{route="{route}",status=~"5.."}}[2m]
        )
      )
      /
      sum(
        rate(
          app_requests_total{{route="{route}"}}[2m]
        )
      )
    )
    '''

    # --------------------------------------------------
    # MAX LATENCY
    # --------------------------------------------------

    max_query = f'''
    max_over_time(
      app_request_duration_seconds_sum{{route="{route}"}}[5m]
    )
    '''

    # --------------------------------------------------
    # THROUGHPUT
    # --------------------------------------------------

    throughput_query = f'''
    sum(
      rate(
        app_request_duration_seconds_count{{route="{route}"}}[1m]
      )
    )
    '''

    # --------------------------------------------------
    # Execute all queries
    # --------------------------------------------------

    metrics = {

        "p95": run_query(p95_query),

        "p99": run_query(p99_query),

        "avg": run_query(avg_query),

        "error_rate": run_query(error_query),

        "max_latency": run_query(max_query),

        "throughput": run_query(throughput_query)
    }

    return metrics

def query_prometheus_metrics_optimized():
    # ---------------------------------------------------
    # Helper
    # ---------------------------------------------------

    def run_query(query):

        try:

            response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})

            data = response.json()

            return data.get("data", {}).get("result", [])

        except Exception as e:

            print(f"Prometheus query failed: {e}")

            return []

    # ---------------------------------------------------
    # Queries
    # ---------------------------------------------------

    queries = {

        "p95": '''
        histogram_quantile(
          0.95,
          sum(
            rate(app_request_duration_seconds_bucket[2m])
          ) by (le, route)
        )
        ''',

        "p99": '''
        histogram_quantile(
          0.99,
          sum(
            rate(app_request_duration_seconds_bucket[2m])
          ) by (le, route)
        )
        ''',

        "avg": '''
        sum(rate(app_request_duration_seconds_sum[2m])) by (route)
        /
        sum(rate(app_request_duration_seconds_count[2m])) by (route)
        ''',

        "error_rate": '''
        (
          sum(
            rate(app_requests_total{status=~"5.."}[2m])
          ) by (route)
          /
          sum(
            rate(app_requests_total[2m])
          ) by (route)
        )
        ''',

        "max_latency": '''
        max (
            max_over_time(
                app_request_duration_seconds_sum[5m]
            )
        ) by (route)
        ''',

        "throughput": '''
        sum(
          rate(app_request_duration_seconds_count[1m])
        ) by (route)
        '''
    }

    # ---------------------------------------------------
    # Final metrics object
    # ---------------------------------------------------

    final_metrics = {}

    # ---------------------------------------------------
    # Execute queries
    # ---------------------------------------------------

    for metric_name, query in queries.items():

        results = run_query(query)
        #print(f"Raw results for {metric_name}:", results, flush=True)

        for item in results:

            route = item["metric"].get("route")

            if not route:
                continue

            value = item["value"][1]

            try:
                value = round(float(value), 4)
            except:
                value = 0

            if route not in final_metrics:

                final_metrics[route] = {}

            final_metrics[route][metric_name] = value

    # ---------------------------------------------------
    # Fill missing metrics
    # ---------------------------------------------------

    required_metrics = [
        "p95",
        "p99",
        "avg",
        "error_rate",
        "max_latency",
        "throughput"
    ]

    #print("Raw metrics from Prometheus:", final_metrics, flush=True)

    for route in final_metrics:

        for metric in required_metrics:

            if metric not in final_metrics[route]:

                final_metrics[route][metric] = 0

    return final_metrics
