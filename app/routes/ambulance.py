from flask import Blueprint, render_template, request, jsonify
from app import socketio
import math

ambulance_bp = Blueprint("ambulance", __name__)

# ── Hospitals DB (replace with real MySQL query) ───────────────
HOSPITALS = [
    {"id": 1,  "name": "AIIMS Bhubaneswar",           "lat": 20.2525, "lng": 85.8118, "city": "Bhubaneswar", "district": "Khordha",
     "specialty": "Cardiac ICU",      "er": True,  "beds": 12, "trauma": True,  "neuro": False, "burns": False, "obstetric": True,  "zone_id": 1, "rating": 4.8},
    {"id": 2,  "name": "Apollo Hospitals",             "lat": 20.3017, "lng": 85.8176, "city": "Bhubaneswar", "district": "Khordha",
     "specialty": "Multi-specialty",  "er": True,  "beds": 8,  "trauma": True,  "neuro": True,  "burns": False, "obstetric": True,  "zone_id": 1, "rating": 4.6},
    {"id": 3,  "name": "Capital Hospital",             "lat": 20.2730, "lng": 85.8440, "city": "Bhubaneswar", "district": "Khordha",
     "specialty": "General Emergency","er": True,  "beds": 20, "trauma": True,  "neuro": False, "burns": False, "obstetric": True,  "zone_id": 1, "rating": 4.2},
    {"id": 4,  "name": "SCB Medical College",          "lat": 20.4625, "lng": 85.8830, "city": "Cuttack",     "district": "Cuttack",
     "specialty": "Trauma & Burns",   "er": True,  "beds": 30, "trauma": True,  "neuro": True,  "burns": True,  "obstetric": True,  "zone_id": 2, "rating": 4.1},
    {"id": 5,  "name": "Hi-Tech Medical College",      "lat": 20.3400, "lng": 85.8200, "city": "Bhubaneswar", "district": "Khordha",
     "specialty": "Neuro & Spine",    "er": True,  "beds": 6,  "trauma": False, "neuro": True,  "burns": False, "obstetric": False, "zone_id": 1, "rating": 4.3},
    {"id": 6,  "name": "SUM Hospital",                 "lat": 20.2960, "lng": 85.8100, "city": "Bhubaneswar", "district": "Khordha",
     "specialty": "Multi-specialty",  "er": True,  "beds": 10, "trauma": True,  "neuro": True,  "burns": False, "obstetric": True,  "zone_id": 1, "rating": 4.4},
    {"id": 7,  "name": "Sparsh Hospital",              "lat": 20.3200, "lng": 85.8150, "city": "Bhubaneswar", "district": "Khordha",
     "specialty": "Ortho & Trauma",   "er": True,  "beds": 5,  "trauma": True,  "neuro": False, "burns": False, "obstetric": False, "zone_id": 1, "rating": 4.0},
    {"id": 8,  "name": "Ispat General Hospital",       "lat": 22.0330, "lng": 84.7980, "city": "Rourkela",   "district": "Sundargarh",
     "specialty": "General Emergency","er": True,  "beds": 15, "trauma": True,  "neuro": False, "burns": True,  "obstetric": True,  "zone_id": 3, "rating": 3.9},
]

# ── Specialty → condition mapping ─────────────────────────────
CONDITION_SPECIALTY = {
    "cardiac":     ["Cardiac ICU", "Multi-specialty"],
    "stroke":      ["Neuro & Spine", "Multi-specialty"],
    "trauma":      ["Trauma & Burns", "Ortho & Trauma", "Multi-specialty"],
    "respiratory": ["Multi-specialty", "General Emergency"],
    "burns":       ["Trauma & Burns"],
    "obstetric":   ["Multi-specialty", "General Emergency"],
    "poisoning":   ["General Emergency", "Multi-specialty"],
    "general":     ["General Emergency", "Multi-specialty"],
}

CONDITION_CAPABILITY = {
    "cardiac":     "er",
    "stroke":      "neuro",
    "trauma":      "trauma",
    "burns":       "burns",
    "obstetric":   "obstetric",
    "respiratory": "er",
    "poisoning":   "er",
    "general":     "er",
}


def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def score_hospital(h, vitals, condition, severity, lat, lng):
    """
    ML-style weighted scoring.
    Weights tuned to clinical priority:
      - Specialty match  35%
      - Distance         25%
      - Bed availability 15%
      - Capability match 15%
      - Severity urgency 10%
    """
    dist = haversine(lat, lng, h["lat"], h["lng"])

    # 1. Specialty match (0–35)
    preferred = CONDITION_SPECIALTY.get(condition, ["General Emergency"])
    specialty_score = 35 if h["specialty"] in preferred else 10

    # 2. Distance score (0–25) — inverse, capped at 50km
    dist_score = max(0, 25 - (dist / 50) * 25)

    # 3. Bed availability (0–15)
    bed_score = min(15, h["beds"] * 1.5)

    # 4. Capability match (0–15)
    cap_key = CONDITION_CAPABILITY.get(condition, "er")
    cap_score = 15 if h.get(cap_key, False) else 5

    # 5. Severity urgency — critical cases need ER (0–10)
    urgency_score = 0
    if severity == "critical":
        urgency_score = 10 if h["er"] else 0
    elif severity == "serious":
        urgency_score = 7 if h["er"] else 3
    else:
        urgency_score = 5

    # Vital-based bonus: low SpO2 → prefer respiratory/ICU
    vital_bonus = 0
    spo2 = vitals.get("spo2")
    gcs  = vitals.get("gcs")
    bp   = vitals.get("bp_sys")
    if spo2 and float(spo2) < 90 and "ICU" in h["specialty"]:
        vital_bonus += 5
    if gcs and float(gcs) <= 8 and h.get("neuro"):
        vital_bonus += 5
    if bp and float(bp) < 80 and h["er"]:
        vital_bonus += 5

    total = specialty_score + dist_score + bed_score + cap_score + urgency_score + vital_bonus
    return round(min(100, total)), round(dist, 1)


def build_ai_reason(h, condition, severity, dist, vitals):
    reasons = []
    preferred = CONDITION_SPECIALTY.get(condition, [])
    if h["specialty"] in preferred:
        reasons.append(f"Specialty matches {condition} case ({h['specialty']})")
    if dist < 5:
        reasons.append(f"Closest at {dist} km — faster arrival saves critical minutes")
    if h["er"]:
        reasons.append("24/7 ER with trauma team on standby")
    if h.get("neuro") and condition == "stroke":
        reasons.append("Neuro-ICU available for stroke protocol")
    if h.get("burns") and condition == "burns":
        reasons.append("Dedicated burns unit with skin bank")
    if h["beds"] >= 10:
        reasons.append(f"{h['beds']} ICU beds available")
    spo2 = vitals.get("spo2")
    if spo2 and float(spo2) < 90:
        reasons.append("Critical SpO₂ — ICU ventilator support available here")
    if not reasons:
        reasons.append(f"Rated {h['rating']}/5 · Capable general emergency care")
    return ". ".join(reasons[:3]) + "."


# ── Routes ─────────────────────────────────────────────────────

@ambulance_bp.route("/ambulance")
def ambulance():
    return render_template("ambulance.html")


@ambulance_bp.route("/api/ambulance-recommend", methods=["POST"])
def ambulance_recommend():
    data = request.get_json()
    lat       = float(data.get("lat", 20.2961))
    lng       = float(data.get("lng", 85.8245))
    condition = data.get("condition", "general")
    severity  = data.get("severity", "serious")
    vitals    = {k: data.get(k) for k in ["spo2","gcs","bp_sys","bp_dia","pulse","temp","glucose","rr"]}

    scored = []
    for h in HOSPITALS:
        score, dist = score_hospital(h, vitals, condition, severity, lat, lng)
        eta = round((dist / 60) * 60 + 3)   # avg 60 km/h + 3 min prep
        scored.append({
            "id":           h["id"],
            "name":         h["name"],
            "lat":          h["lat"],
            "lng":          h["lng"],
            "city":         h["city"],
            "district":     h["district"],
            "specialty":    h["specialty"],
            "er_available": h["er"],
            "beds":         h["beds"],
            "rating":       h["rating"],
            "distance_km":  dist,
            "eta_min":      eta,
            "score":        score,
            "ai_reason":    build_ai_reason(h, condition, severity, dist, vitals),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:5]

    summary = f"{severity.capitalize()} · {condition.capitalize()} · {len(top)} hospitals ranked"

    # Notify hospital dashboard via SocketIO
    socketio.emit("ambulance_vitals_update", {
        "condition": condition,
        "severity":  severity,
        "vitals":    vitals,
        "top_hospital": top[0]["name"] if top else "N/A",
        "eta_min":   top[0]["eta_min"] if top else "?",
    })

    return jsonify({"recommendations": top, "summary": summary})
