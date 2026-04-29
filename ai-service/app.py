from flask import Flask, request, jsonify

import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
