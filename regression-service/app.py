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
