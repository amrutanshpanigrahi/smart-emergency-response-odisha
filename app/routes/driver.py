from flask import Blueprint, request, jsonify, render_template
from app import socketio

driver_bp = Blueprint("driver", __name__)


# ── Pages ────────────────────────────────────────────────────────
@driver_bp.route("/driver")
def driver():
    return render_template("driver.html")


# ── API: Driver pushes GPS location ─────────────────────────────
@driver_bp.route("/api/update-location", methods=["POST"])
def update_location():
    data = request.get_json()

    # Broadcast to patient and hospital
    socketio.emit("ambulance_location", {
        "ambulance_id": data.get("ambulance_id"),
        "incident_id":  data.get("incident_id"),
        "lat":          data.get("lat"),
        "lng":          data.get("lng"),
        "eta_min":      data.get("eta_min", 0)
    })

    return jsonify({"status": "ok"})


# ── API: Driver marks arrived at patient or hospital ─────────────
@driver_bp.route("/api/mark-arrived", methods=["POST"])
def mark_arrived():
    data  = request.get_json()
    stage = data.get("stage")

    socketio.emit("ambulance_arrived", {
        "incident_id": data.get("incident_id"),
        "stage":       stage
    })

    return jsonify({"status": "ok", "stage": stage})