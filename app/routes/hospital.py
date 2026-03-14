from flask import Blueprint, request, jsonify, render_template
from app import socketio

hospital_bp = Blueprint("hospital", __name__)


# ── Pages ────────────────────────────────────────────────────────
@hospital_bp.route("/hospital")
def hospital():
    return render_template("hospital.html")

@hospital_bp.route("/zone-map")
def zone_map():
    return render_template("zone_map.html")


# ── API: Update prep checklist item ─────────────────────────────
@hospital_bp.route("/api/prep-status", methods=["POST"])
def prep_status():
    data = request.get_json()

    socketio.emit("prep_updated", {
        "incident_id": data.get("incident_id"),
        "item":        data.get("item"),
        "status":      data.get("status")
    })

    return jsonify({"status": "ok"})


# ── API: Hospital acknowledges alert ────────────────────────────
@hospital_bp.route("/api/acknowledge", methods=["POST"])
def acknowledge():
    data = request.get_json()

    socketio.emit("alert_acknowledged", {
        "incident_id":  data.get("incident_id"),
        "hospital_id":  data.get("hospital_id"),
        "acknowledged": True
    })

    return jsonify({"status": "acknowledged"})