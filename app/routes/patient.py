from flask import Blueprint, request, jsonify, render_template
from app import socketio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../ml"))
from zone_classifier import load_and_preprocess, train_and_assign, ai_recommend

patient_bp = Blueprint("patient", __name__)

# Load ML model once at startup
_df = None
def get_df():
    global _df
    if _df is None:
        raw = load_and_preprocess()
        _df = train_and_assign(raw)
    return _df


# ── Pages ────────────────────────────────────────────────────────
@patient_bp.route("/")
def index():
    return render_template("patient.html")


# ── API: Get nearby hospitals with AI ranking ────────────────────
@patient_bp.route("/api/recommend", methods=["POST"])
def recommend():
    data     = request.get_json()
    lat      = float(data.get("lat",      20.2961))
    lng      = float(data.get("lng",      85.8245))
    symptom  = data.get("symptom",  "general")
    severity = data.get("severity", "medium")

    df   = get_df()
    recs = ai_recommend(lat, lng, symptom, severity, df, top_n=5)

    return jsonify({
        "recommendations": recs,
        "severity":        severity,
        "symptom":         symptom
    })


# ── API: Patient calls ambulance ─────────────────────────────────
@patient_bp.route("/api/call-ambulance", methods=["POST"])
def call_ambulance():
    data = request.get_json()

    # Emit to all drivers (in production filter by nearest driver room)
    socketio.emit("new_incident", {
        "incident_id":    1001,
        "patient_name":   data.get("patient_name",  "Patient"),
        "age_gender":     data.get("age_gender",    "Unknown"),
        "symptom":        data.get("symptom",       "General"),
        "blood_group":    data.get("blood_group",   "Unknown"),
        "hospital_name":  data.get("hospital_name", "Unknown"),
        "hospital_lat":   data.get("hospital_lat",  0),
        "hospital_lng":   data.get("hospital_lng",  0),
        "patient_lat":    data.get("lat",           0),
        "patient_lng":    data.get("lng",           0),
        "eta_patient_min":  6,
        "eta_hospital_min": 14,
        "total_dist_km":    4.2,
        "ai_reason":      data.get("ai_reason", "")
    })

    # Emit to hospital
    socketio.emit("hospital_alert", {
        "patient_name": data.get("patient_name", "Patient"),
        "symptom":      data.get("symptom",      "General"),
        "blood_group":  data.get("blood_group",  "Unknown"),
        "zone_name":    data.get("zone_name",    "Unknown"),
        "eta_min":      14,
        "ai_reason":    data.get("ai_reason",    "")
    })

    return jsonify({"status": "dispatched", "incident_id": 1001})