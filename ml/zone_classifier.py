"""
IERN Zone Classifier + AI Recommendation Engine
K-Means clustering on Odisha hospital CSV data.
Zones hospitals by rating, availability, bed count, and geography.
"""

import pandas as pd
import numpy as np
import json
import pickle
import os
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from math import radians, sin, cos, sqrt, atan2

# ── Zone labels ──────────────────────────────────────────────────
ZONE_META = {
    0: {"name": "Zone A – Critical Care Hub",  "color": "#E24B4A", "priority": 1,
        "desc": "Top-rated, high-capacity hospitals. Best for severe emergencies."},
    1: {"name": "Zone B – Regional Centre",    "color": "#EF9F27", "priority": 2,
        "desc": "Good-rated regional hospitals. Handles most emergency cases."},
    2: {"name": "Zone C – District Hospital",  "color": "#378ADD", "priority": 3,
        "desc": "Moderate-rated district hospitals. Suitable for stable patients."},
    3: {"name": "Zone D – Basic Facility",     "color": "#888780", "priority": 4,
        "desc": "Lower-rated or rural facilities. First-contact only."},
}

BASE_DIR   = os.path.dirname(__file__)
CSV_PATH   = os.path.join(BASE_DIR, "../data/odisha_hospitals.csv")
MODEL_PATH = os.path.join(BASE_DIR, "zone_model.pkl")
OUT_PATH   = os.path.join(BASE_DIR, "../data/hospitals_zoned.json")


# ── Haversine distance (no external library needed) ──────────────
def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ── Load CSV ─────────────────────────────────────────────────────
def load_and_preprocess():
    df = pd.read_csv(CSV_PATH)
    df["er_available"] = df["er_available"].astype(int)
    df["beds"]         = df["beds"].fillna(0)
    df["rating"]       = df["rating"].fillna(df["rating"].mean())
    return df


# ── Build feature matrix ─────────────────────────────────────────
def build_features(df):
    features = df[["rating", "beds", "er_available", "lat", "lng"]].copy()
    features["rating"]       *= 2.0   # weight rating higher
    features["er_available"] *= 1.5   # weight ER availability higher
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(features)
    return X_scaled, scaler


# ── Train K-Means ─────────────────────────────────────────────────
def train_and_assign(df):
    X, scaler = build_features(df)
    n_zones   = 4

    km = KMeans(n_clusters=n_zones, random_state=42, n_init=15)
    km.fit(X)

    # Map cluster IDs so Zone 0 = highest rated cluster
    centroids_df = pd.DataFrame(
        km.cluster_centers_,
        columns=["rating", "beds", "er", "lat", "lng"]
    )
    order = centroids_df["rating"].argsort()[::-1].values
    remap = {old: new for new, old in enumerate(order)}
    labels = np.array([remap[l] for l in km.labels_])

    df = df.copy()
    df["zone_id"]    = labels
    df["zone_name"]  = df["zone_id"].map(lambda z: ZONE_META[z]["name"])
    df["zone_color"] = df["zone_id"].map(lambda z: ZONE_META[z]["color"])

    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": km, "scaler": scaler, "remap": remap}, f)

    print("=== Zone Classification Results ===")
    print(df.groupby(["zone_id", "zone_name"])["id"].count().rename("hospitals"))
    return df


# ── AI Recommendation Engine ──────────────────────────────────────
def ai_recommend(patient_lat, patient_lng, symptom, severity, df, top_n=5):

    SEVERITY_WEIGHTS = {
        "high":   {"dist": 0.50, "rating": 0.25, "zone": 0.15, "er": 0.07, "spec": 0.03},
        "medium": {"dist": 0.35, "rating": 0.30, "zone": 0.20, "er": 0.10, "spec": 0.05},
        "low":    {"dist": 0.25, "rating": 0.30, "zone": 0.25, "er": 0.10, "spec": 0.10},
    }

    SPECIALTY_MAP = {
        "chest pain":  ["Cardiac", "Multi-Specialty"],
        "stroke":      ["Neuro", "Multi-Specialty"],
        "accident":    ["Trauma", "Multi-Specialty", "Ortho"],
        "cancer":      ["Oncology", "Multi-Specialty"],
        "fracture":    ["Ortho & Spine", "Multi-Specialty"],
        "general":     ["General", "Multi-Specialty"],
        "breathing":   ["Multi-Specialty", "Cardiac"],
        "unconscious": ["Multi-Specialty"],
    }

    w         = SEVERITY_WEIGHTS.get(severity, SEVERITY_WEIGHTS["medium"])
    sym_key   = next((k for k in SPECIALTY_MAP if k in symptom.lower()), "general")
    pref_spec = SPECIALTY_MAP[sym_key]

    # For high severity only show hospitals with ER
    rows = df[df["er_available"] == 1].copy() if severity == "high" else df.copy()

    results = []
    for _, h in rows.iterrows():
        dist_km = haversine_km(patient_lat, patient_lng, h["lat"], h["lng"])
        if dist_km > 300:
            continue

        zone_priority = ZONE_META[int(h["zone_id"])]["priority"]
        spec_match    = 1.0 if any(s in str(h["specialty"]) for s in pref_spec) else 0.0
        er_bonus      = float(h["er_available"])
        rating_norm   = float(h["rating"]) / 5.0
        dist_score    = 1.0 / (dist_km + 0.5)
        zone_score    = 1.0 / zone_priority

        score = (w["dist"]   * dist_score  +
                 w["rating"] * rating_norm +
                 w["zone"]   * zone_score  +
                 w["er"]     * er_bonus    +
                 w["spec"]   * spec_match)

        # Build human-readable reason
        reasons = []
        if spec_match:
            reasons.append(f"Specialises in {h['specialty']}")
        if int(h["zone_id"]) == 0:
            reasons.append("Top-rated Critical Care Hub")
        elif int(h["zone_id"]) == 1:
            reasons.append("Regional centre with good capacity")
        if dist_km < 5:
            reasons.append(f"Very close ({dist_km:.1f} km)")
        elif dist_km < 15:
            reasons.append(f"{dist_km:.1f} km away")
        else:
            reasons.append(f"{dist_km:.1f} km away")
        if er_bonus:
            reasons.append("ER open 24/7")
        if float(h["rating"]) >= 4.3:
            reasons.append(f"Highly rated ({h['rating']}★)")

        results.append({
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
            "distance_km": round(dist_km, 2),
            "score":       round(score, 4),
            "ai_reason":   " · ".join(reasons) if reasons else "Available facility",
            "ai_badge":    _badge(score, dist_km, int(h["zone_id"])),
        })

    results.sort(key=lambda x: -x["score"])
    return results[:top_n]


def _badge(score, dist_km, zone_id):
    if zone_id == 0 and dist_km < 20:
        return {"label": "Best match",   "color": "#1D9E75"}
    if score > 0.4:
        return {"label": "Recommended",  "color": "#378ADD"}
    if dist_km < 5:
        return {"label": "Nearest",      "color": "#EF9F27"}
    return     {"label": "Available",    "color": "#888780"}


# ── Export GeoJSON for Leaflet map ────────────────────────────────
def export_geojson(df):
    features = []
    for _, h in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(h["lng"]), float(h["lat"])]
            },
            "properties": {
                "id":         int(h["id"]),
                "name":       h["name"],
                "city":       h["city"],
                "rating":     float(h["rating"]),
                "beds":       int(h["beds"]),
                "er":         int(h["er_available"]),
                "specialty":  h["specialty"],
                "zone_id":    int(h["zone_id"]),
                "zone_name":  h["zone_name"],
                "zone_color": h["zone_color"],
                "phone":      h["phone"],
                "type":       h["type"],
            }
        })
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "zone_meta": ZONE_META
    }
    with open(OUT_PATH, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"GeoJSON saved → {OUT_PATH}")
    return geojson


# ── Run directly to test ──────────────────────────────────────────
if __name__ == "__main__":
    print("=== IERN Zone Classifier ===")
    df     = load_and_preprocess()
    df_out = train_and_assign(df)
    export_geojson(df_out)

    print("\nSample AI recommendations (Bhubaneswar, chest pain, high severity):")
    recs = ai_recommend(20.2961, 85.8245, "chest pain", "high", df_out, top_n=3)
    for i, r in enumerate(recs, 1):
        print(f"  {i}. {r['name']} [{r['zone_name']}]")
        print(f"     {r['distance_km']} km · score {r['score']} · {r['ai_reason']}")
