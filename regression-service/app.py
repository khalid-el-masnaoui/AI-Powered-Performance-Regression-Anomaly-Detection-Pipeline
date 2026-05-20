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

def query_history(route):

    # ---------------------------------------------------
    # Helper
    # ---------------------------------------------------

    def run_query(query):

        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                "query": query,
                "start": time.time() - 3600,
                "end": time.time(),
                "step": 20
            }
        )

        data = response.json()

        results = data.get("data", {}).get("result", [])

        #print(f"History query results for {route}:", results, flush=True)

        if not results:
            return []

        return results[0]["values"]

    # ---------------------------------------------------
    # Queries
    # ---------------------------------------------------

    queries = {

        "p95": f'''
        histogram_quantile(
          0.95,
          sum(
            rate(
              app_request_duration_seconds_bucket{{route="{route}"}}[5m]
            )
          ) by (le)
        )
        ''',

        "p99": f'''
        histogram_quantile(
          0.99,
          sum(
            rate(
              app_request_duration_seconds_bucket{{route="{route}"}}[5m]
            )
          ) by (le)
        )
        ''',

        "avg": f'''
        sum(
          rate(
            app_request_duration_seconds_sum{{route="{route}"}}[5m]
          )
        )
        /
        sum(
          rate(
            app_request_duration_seconds_count{{route="{route}"}}[5m]
          )
        )
        ''',

        "error_rate": f'''
        sum(
          rate(
            app_requests_total{{route="{route}",status=~"5.."}}[5m]
          )
        )
        /
        sum(
          rate(
            app_requests_total{{route="{route}"}}[5m]
          )
        )
        ''',

        "throughput": f'''
        sum(
          rate(
            app_request_duration_seconds_count{{route="{route}"}}[1m]
          )
        )
        ''',

        "max_latency": f'''
        max_over_time(
          app_request_duration_seconds_sum{{route="{route}"}}[5m]
        )
        '''

    
    }

    # ---------------------------------------------------
    # Execute queries
    # ---------------------------------------------------

    raw = {}

    for metric_name, query in queries.items():

        raw[metric_name] = run_query(query)

    # ---------------------------------------------------
    # Merge by timestamp
    # ---------------------------------------------------

    history = {}

    for metric_name, values in raw.items():

        for item in values:

            timestamp = int(item[0])

            value = item[1]

            try:
                value = round(float(value), 4)
            except:
                value = 0

            if timestamp not in history:

                history[timestamp] = {
                    "timestamp": timestamp
                }

            history[timestamp][metric_name] = value

    # ---------------------------------------------------
    # Normalize missing fields
    # ---------------------------------------------------

    required = [
        "p95",
        "p99",
        "avg",
        "error_rate",
        "throughput",
        "max_latency"
    ]

    final = []

    for ts in sorted(history.keys()):

        row = history[ts]

        for metric in required:

            if metric not in row:
                row[metric] = 0

        final.append(row)

    return final

# -------------------------
# SPX trigger
# -------------------------
def trigger_spx(route):
    # Enable profiling for next requests
    r.setex(f"spx:{route}", 60, 1)


# -------------------------
# Slack notification
# -------------------------
def send_slack(payload):
    try:
        requests.post(SLACK_WEBHOOK, json=payload)
    except Exception as e:
        print("Slack error:", e)

def build_slack_payload(route, result):

    def fmt(value):
        try:
            return f"{float(value):.2f}"
        except:
            return "0.00"

    baseline = result.get("baseline", {})

    current = result.get("current", {})

    ai = result.get("ai", {})

    increase = result.get("increase", {})

    regression = result.get("regression", False)

    payload = {

        "attachments": [

            {

                "color":
                    "#ff0000"
                    if regression
                    else "#36a64f",

                "title":
                    f"🚨 Performance Alert: {route}",

                "fields": [

                    # -----------------------------------
                    # Regression State
                    # -----------------------------------

                    {
                        "title": "Regression",
                        "value": str(regression),
                        "short": True
                    },

                    {
                        "title": "Severity",
                        "value": ai.get(
                            "severity",
                            "N/A"
                        ),
                        "short": True
                    },

                    {
                        "title": "Anomaly Score",
                        "value": fmt(
                            ai.get(
                                "anomaly_score",
                                0
                            )
                        ),
                        "short": True
                    },

                    {
                        "title": "Confidence",
                        "value": fmt(
                            ai.get(
                                "confidence",
                                0
                            )
                        ),
                        "short": True
                    },

                    # -----------------------------------
                    # P95
                    # -----------------------------------

                    {
                        "title": "Current p95",
                        "value":
                            f"{fmt(current.get('p95', 0))}s",
                        "short": True
                    },

                    {
                        "title": "Baseline p95",
                        "value":
                            f"{fmt(baseline.get('p95', 0))}s",
                        "short": True
                    },

                    {
                        "title": "p95 Increase",
                        "value":
                            increase.get('p95', '0.00%'),
                        "short": True
                    },

                    # -----------------------------------
                    # P99
                    # -----------------------------------

                    {
                        "title": "Current p99",
                        "value":
                            f"{fmt(current.get('p99', 0))}s",
                        "short": True
                    },

                    {
                        "title": "Baseline p99",
                        "value":
                            f"{fmt(baseline.get('p99', 0))}s",
                        "short": True
                    },

                    {
                        "title": "p99 Increase",
                        "value":
                            increase.get('p99', '0.00%'),
                        "short": True
                    },

                    # -----------------------------------
                    # AVG
                    # -----------------------------------

                    {
                        "title": "Current AVG",
                        "value":
                            f"{fmt(current.get('avg', 0))}s",
                        "short": True
                    },

                    {
                        "title": "Baseline AVG",
                        "value":
                            f"{fmt(baseline.get('avg', 0))}s",
                        "short": True
                    },

                    {
                        "title": "AVG Increase",
                        "value":
                            increase.get('avg', '0.00%'),
                        "short": True
                    },

                    # -----------------------------------
                    # Throughput
                    # -----------------------------------

                    {
                        "title": "Current Throughput",
                        "value":
                            f"{fmt(current.get('throughput', 0))} req/s",
                        "short": True
                    },

                    {
                        "title": "Baseline Throughput",
                        "value":
                            f"{fmt(baseline.get('throughput', 0))} req/s",
                        "short": True
                    },

                    {
                        "title": "Throughput Change",
                        "value":
                            increase.get('throughput', '0.00%'),
                        "short": True
                    },

                    # -----------------------------------
                    # Error Rate
                    # -----------------------------------

                    {
                        "title": "Current Error Rate",
                        "value":
                            f"{fmt(current.get('error_rate', 0) * 100)}%",
                        "short": True
                    },

                    {
                        "title": "Baseline Error Rate",
                        "value":
                            f"{fmt(baseline.get('error_rate', 0) * 100)}%",
                        "short": True
                    },

                    {
                        "title": "Error Rate Change",
                        "value":
                            increase.get('error_rate', '0.00%'),
                        "short": True
                    },

                    # -----------------------------------
                    # Max Latency
                    # -----------------------------------

                    {
                        "title": "Current Max Latency",
                        "value":
                            f"{fmt(current.get('max_latency', 0))}s",
                        "short": True
                    },

                    {
                        "title": "Baseline Max Latency",
                        "value":
                            f"{fmt(baseline.get('max_latency', 0))}s",
                        "short": True
                    },

                    {
                        "title": "Max Latency Change",
                        "value":
                            increase.get('max_latency', '0.00%'),
                        "short": True
                    },
                ],

                "footer": "AI Regression Service",

                "ts": __import__("time").time()
            }
        ]
    }

    return payload

# -------------------------
# baseline PDF report
# -------------------------
def generate_baseline_report(route, payload):

    try:

        requests.post(
            f"{REPORT_URL}/generate-baseline",
            json={
                "route": route,
                "p95": payload["p95"],
                "p99": payload["p99"],
                "avg": payload["avg"],
                "error_rate": payload["error_rate"],
                "max_latency": payload["max_latency"],
                "throughput": payload["throughput"]
            },
            timeout=5
        )

        print(f"📄 Baseline report generated for {route}")

    except Exception as e:

        print("Baseline report error:", e)

# -------------------------
# Regression PDF report
# -------------------------
def generate_report(data):
    try:
        requests.post(f"{REPORT_URL}/generate", json=data)
    except Exception as e:
        print("Report error:", e)

# -------------------------
# Clean data helper
# -------------------------
def clean_data(data):

    if isinstance(data, dict):

        for k, v in data.items():

            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                data[k] = 0

            elif isinstance(v, (dict, list)):
                clean_data(v)

    elif isinstance(data, list):

        for item in data:
            clean_data(item)

    return data

# -------------------------
# Store baseline per route
# -------------------------
@app.route("/baseline", methods=["POST"])
def baseline():
    data = request.json

    route = data["route"]

    payload = {
        "p95": data.get("p95", 0),
        "p99": data.get("p99", 0),
        "avg": data.get("avg", 0),
        "error_rate": data.get("error_rate", 0),
        "max_latency": data.get("max_latency", 0),
        "throughput": data.get("throughput", 0),
        "updated_at": int(time.time())
    }

    r.set(f"baseline:{route}", json.dumps(payload))

    generate_baseline_report(route, payload)

    return jsonify({"status": "stored", "route": route})


# -------------------------
# Alert handler (MAIN ENTRYPOINT)
# -------------------------
@app.route("/alert", methods=["POST"])
def alert():
    payload = request.json

    #print ("alert received", flush=True)
    #print (payload, flush=True)

    results = []

    for alert in payload.get("alerts", []):
        labels = alert.get("labels", {})
        route = labels.get("route")

        if not route:
            continue

        # load baseline
        baseline_raw = r.get(f"baseline:{route}")
        if not baseline_raw:
            print(f"No baseline for {route}", flush=True)
            continue

        baseline = json.loads(baseline_raw)

        if baseline["p95"] == 0:
            continue

        # current latency
        #current = query_prometheus_p95(route)

        # metrics
        #current = query_prometheus_metrics(route)
        current = query_prometheus_metrics_optimized().get(route, {})

        if not current:
            continue

        #print(f"Current metrics for {route}: {current}", flush=True)

        history = query_history(route) or []

        if not history:
            print(f"No history for {route}", flush=True)
            continue
    
        #print(f"Current history for {route}: {history}", flush=True)

        # manual history data for testing anomaly detection (running the k6 tests to trigger anomaly detection can take long)
        try:

            #print(f"Sending data to AI service for {route}...", flush=True)

            ai = requests.post(
                f"{AI_ANOMALY_DETECTION_URL}/detect",
                json=clean_data({
                    "route": route,
                    "history": history,
                    "current": current,
                    "baseline": baseline
                })
            ).json()

        except requests.exceptions.RequestException:
            # Network errors, timeout, connection refused, etc.
            print(f"AI service request failed for {route}", flush=True)
            ai = {}

        print(f"AI response for {route}:", ai, flush=True)

        if not ai:
            continue


        is_regression = ai["regression"]

        print(f"Route: {route}, Regression: {is_regression}", flush=True)

        if is_regression:
            result = {
                "route": route,
                "baseline": baseline,
                "current": current,
                "increase": {
                    "p95": f'{((current["p95"] - baseline["p95"]) / baseline["p95"]) * 100:.2f}%' if baseline["p95"] > 0 else '0%',
                    "p99": f'{((current["p99"] - baseline["p99"]) / baseline["p99"]) * 100:.2f}%' if baseline["p99"] > 0 else '0%',
                    "avg": f'{((current["avg"] - baseline["avg"]) / baseline["avg"]) * 100:.2f}%' if baseline["avg"] > 0 else '0%',
                    "error_rate": f'{((current["error_rate"] - baseline["error_rate"]) / baseline["error_rate"]) * 100:.2f}%' if baseline["error_rate"] > 0 else '0%',
                    "max_latency": f'{((current["max_latency"] - baseline["max_latency"]) / baseline["max_latency"]) * 100:.2f}%' if baseline["max_latency"] > 0 else '0%',
                    "throughput": f'{((current["throughput"] - baseline["throughput"]) / baseline["throughput"]) * 100:.2f}%' if baseline["throughput"] > 0 else '0%'
                },
                "regression": is_regression,
                "ai": ai
            }

            results.append(result)

            # ALWAYS trigger SPX
            trigger_spx(route)

            # ALWAYS notify Slack (even duplicates)
            send_slack(build_slack_payload(route,result))

            # generate report
            generate_report({route: result})
            


    return jsonify({"results": results})


# -------------------------
# Manual check endpoint
# -------------------------
@app.route("/check", methods=["POST"])
def check():
    routes = [key.replace("baseline:", "") for key in r.keys("baseline:*")]

    results = []

    for route in routes:
        baseline = json.loads(r.get(f"baseline:{route}"))

        if baseline["p95"] == 0:
            continue

        #current = query_prometheus_p95(route)
        #current = query_prometheus_metrics(route)
        current = query_prometheus_metrics_optimized().get(route, {})

        if not current:
            continue

        history = query_history(route) or []

        if not history:
            print(f"No history for {route}", flush=True)
            continue

        try:

            #print(f"Sending data to AI service for {route}...", flush=True)

            ai = requests.post(
                f"{AI_ANOMALY_DETECTION_URL}/detect",
                json=clean_data({
                    "route": route,
                    "history": history,
                    "current": current,
                    "baseline": baseline
                })
            ).json()

        except requests.exceptions.RequestException:
            # Network errors, timeout, connection refused, etc.
            print(f"AI service request failed for {route}", flush=True)
            ai = {}

        print(f"AI response for {route}:", ai, flush=True)

        if not ai:
            continue

        is_regression = ai["regression"]

        print(f"Route: {route}, Regression: {is_regression}", flush=True)

        if is_regression:
            result = {
                "route": route,
                "baseline": baseline,
                "current": current,
                "increase": {
                    "p95": f'{((current["p95"] - baseline["p95"]) / baseline["p95"]) * 100:.2f}%' if baseline["p95"] > 0 else '0%',
                    "p99": f'{((current["p99"] - baseline["p99"]) / baseline["p99"]) * 100:.2f}%' if baseline["p99"] > 0 else '0%',
                    "avg": f'{((current["avg"] - baseline["avg"]) / baseline["avg"]) * 100:.2f}%' if baseline["avg"] > 0 else '0%',
                    "error_rate": f'{((current["error_rate"] - baseline["error_rate"]) / baseline["error_rate"]) * 100:.2f}%' if baseline["error_rate"] > 0 else '0%',
                    "max_latency": f'{((current["max_latency"] - baseline["max_latency"]) / baseline["max_latency"]) * 100:.2f}%' if baseline["max_latency"] > 0 else '0%',
                    "throughput": f'{((current["throughput"] - baseline["throughput"]) / baseline["throughput"]) * 100:.2f}%' if baseline["throughput"] > 0 else '0%'
                },
                "regression": is_regression,
                "ai": ai
            }

            results.append(result)

    return jsonify(results)


# -------------------------
# health check
# -------------------------
@app.route("/health")
def health():
    return {"status": "ok"}


# -------------------------
# run
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
