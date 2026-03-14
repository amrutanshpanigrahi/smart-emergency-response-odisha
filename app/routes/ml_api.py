from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../ml"))
from zone_classifier import (
    load_and_preprocess,
    train_and_assign,
    ai_recommend,
    ZONE_META
)

ml_bp = Blueprint("ml", __name__)

# Load ML model once at startup
_df = None
def get_df():
    global _df
    if _df is None:
        raw = load_and_preprocess()
        _df = train_and_assign(raw)
    return _df


# ── API: Get all hospitals with zone labels ──────────────────────
@ml_bp.route("/api/zones", methods=["GET"])
def get_zones():
    df = get_df()
    hospitals = []

    for _, h in df.iterrows():
        hospitals.append({
            "id":          int(h["id"]),
            "name":        h["name"],
            "city":        h["city"],
            "district":    h["district"],
            "lat":         float(h["lat"]),
            "lng":         float(h["lng"]),
            "rating":      float(h["rating"]),
            "beds":        int(h["beds"]),
            "er_available":int(h["er_available"]),
            "specialty":   h["specialty"],
            "phone":       h["phone"],
            "type":        h["type"],
            "zone_id":     int(h["zone_id"]),
            "zone_name":   h["zone_name"],
            "zone_color":  h["zone_color"],
        })

    return jsonify({
        "hospitals":  hospitals,
        "zone_meta":  ZONE_META
    })


# ── API: AI recommendation ───────────────────────────────────────
@ml_bp.route("/api/recommend", methods=["POST"])
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


# ── API: Zone statistics ─────────────────────────────────────────
@ml_bp.route("/api/zone-stats", methods=["GET"])
def zone_stats():
    df    = get_df()
    stats = []

    for zone_id, meta in ZONE_META.items():
        sub = df[df["zone_id"] == zone_id]
        stats.append({
            "zone_id":    zone_id,
            "zone_name":  meta["name"],
            "color":      meta["color"],
            "desc":       meta["desc"],
            "count":      int(len(sub)),
            "avg_rating": round(float(sub["rating"].mean()), 2),
            "total_beds": int(sub["beds"].sum()),
            "er_count":   int(sub["er_available"].sum()),
            "hospitals":  sub["name"].tolist(),
        })

    return jsonify(stats)