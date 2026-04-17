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
