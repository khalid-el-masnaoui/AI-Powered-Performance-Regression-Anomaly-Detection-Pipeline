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
