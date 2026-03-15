# 🚑 Smart Emergency Response Odisha

An intelligent ambulance dispatch and hospital routing system for Odisha, built with Python, Flask, MySQL, Machine Learning (K-Means + weighted scoring), and real-time WebSocket communication.

---

## 🌟 Features

- **SOS Emergency Call** — Patient taps SOS, shares live GPS location instantly
- **AI Hospital Recommendations** — Ranked by distance, rating, specialty and zone
- **ML Zone Classification** — 40 Odisha hospitals classified into 4 zones using K-Means clustering
- **Live Ambulance Tracking** — Real-time map tracking via Leaflet.js + OpenStreetMap
- **Driver Tablet UI** — Driver gets patient info, destination and optimal route instantly
- **Hospital Pre-Alert Dashboard** — Hospital is notified before ambulance arrives
- **Prep Checklist** — ER team can tick off preparation tasks in real time
- **Zone Map** — Full Odisha hospital zone map with AI recommender panel
- **🆕 Ambulance Doctor Panel** — On-site doctor enters live vitals; ML model recommends the best capable hospital in real time

---

## 🩺 Ambulance Doctor Panel (New)

A dedicated tablet interface for the attending doctor or paramedic inside the ambulance. After assessing the patient on-site, the doctor enters vitals and the ML engine instantly recommends the nearest capable hospital.

### Vitals captured
- Blood Pressure (systolic / diastolic)
- Pulse / Heart Rate
- SpO₂ (oxygen saturation)
- GCS Score (Glasgow Coma Scale)
- Temperature
- Blood Glucose
- Respiratory Rate
- Physical Injury Description (free text)

### Auto-severity detection
The UI automatically classifies severity as **Critical / Serious / Stable** based on entered vitals using clinical thresholds (SpO₂, GCS, pulse, BP, RR, glucose) — the doctor can override manually.

### ML Scoring Engine
Hospitals are ranked using a weighted scoring formula:

```
score = specialty_match  × 0.35
      + distance_score   × 0.25
      + bed_availability × 0.15
      + capability_match × 0.15   (trauma / neuro / burns / obstetric)
      + severity_urgency × 0.10
      + vital_bonuses              (SpO₂ < 90 → ICU boost, GCS ≤ 8 → neuro boost)
```

### Condition → Specialty mapping
| Condition | Preferred Specialty |
|-----------|-------------------|
| Cardiac / MI | Cardiac ICU, Multi-specialty |
| Stroke / Neuro | Neuro & Spine, Multi-specialty |
| Trauma / Accident | Trauma & Burns, Ortho & Trauma |
| Burns | Trauma & Burns |
| Respiratory | Multi-specialty, General Emergency |
| Obstetric | Multi-specialty, General Emergency |
| Poisoning / OD | General Emergency, Multi-specialty |

### Real-time hospital notification
When the doctor dispatches, the hospital dashboard is instantly notified via SocketIO with the patient's vitals summary, condition, severity, and ETA.

---

## 🗺️ ML Zone Classification

Uses **scikit-learn K-Means (k=4)** clustering on:
- Hospital rating (weight ×2.0)
- Bed count
- ER availability (weight ×1.5)
- Geographic coordinates (lat, lng)

| Zone | Label | Description |
|------|-------|-------------|
| Zone A | Critical Care Hub | Top-rated, high-capacity. Best for severe emergencies |
| Zone B | Regional Centre | Good-rated regional hospitals. Handles most cases |
| Zone C | District Hospital | Moderate-rated. Suitable for stable patients |
| Zone D | Basic Facility | Lower-rated or rural. First-contact only |

---

## 🤖 AI Recommendation Engine (Patient App)

Scores each hospital using a weighted formula:
```
score = w_dist   × (1 / distance)
      + w_rating × (rating / 5)
      + w_zone   × (1 / zone_priority)
      + w_er     × er_available
      + w_spec   × specialty_match
```

Weights shift based on severity:
- **High** → distance 50%, rating 25% (nearest Zone A/B first)
- **Medium** → balanced across all factors
- **Low** → specialty and zone matter more

---

## 🏥 Dataset

`data/odisha_hospitals.csv` — 40 hospitals across Odisha including:

- AIIMS Bhubaneswar, SCB Medical College (Cuttack)
- Apollo Hospitals, SUM Hospital, KIMS Hospital (Bhubaneswar)
- VSS Medical College (Sambalpur)
- MKCG Medical College (Berhampur)
- Ispat General Hospital (Rourkela)
- 20+ district hospitals across all major districts

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + Flask 3.0 |
| Real-time | Flask-SocketIO + eventlet |
| Database | MySQL 8.0 |
| Machine Learning | scikit-learn (K-Means + weighted scoring), pandas, numpy |
| Maps | Leaflet.js + OpenStreetMap (free, no API key) |
| Frontend | HTML5 + CSS3 + Vanilla JavaScript |
| Distance | Haversine formula (pure Python) |

---

## 📁 Project Structure

```
smart-emergency-response-odisha/
├── app/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── patient.py
│       ├── driver.py
│       ├── hospital.py
│       ├── ml_api.py
│       └── ambulance.py          ← new
├── ml/
│   └── zone_classifier.py
├── data/
│   └── odisha_hospitals.csv
├── templates/
│   ├── patient.html
│   ├── driver.html
│   ├── hospital.html
│   ├── zone_map.html
│   └── ambulance.html            ← new
├── schema.sql
├── seed_hospitals.py
├── run.py
└── requirements.txt
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/amrutanshpanigrahi/smart-emergency-response-odisha.git
cd smart-emergency-response-odisha
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up MySQL database
```bash
mysql -u root -p < schema.sql
```

### 4. Add your MySQL password

Open `app/__init__.py` and `seed_hospitals.py` and set:
```python
app.config["MYSQL_PASSWORD"] = "your_password_here"
```

### 5. Run ML training and seed hospitals
```bash
python seed_hospitals.py
```

### 6. Start the server
```bash
python run.py
```

---

## 🌐 Pages

| URL | Description |
|-----|-------------|
| `http://localhost:5000/` | Patient SOS app |
| `http://localhost:5000/driver` | Driver tablet |
| `http://localhost:5000/hospital` | Hospital dashboard |
| `http://localhost:5000/zone-map` | Odisha ML zone map |
| `http://localhost:5000/ambulance` | 🆕 Ambulance doctor panel |

---

## 📡 Real-Time Flow

```
Patient confirms hospital
        ↓
Flask emits → driver:   new_incident      (patient + hospital info)
Flask emits → hospital: hospital_alert    (patient + ETA + AI note)
        ↓
Driver pushes GPS every 5s
        ↓
Flask broadcasts → patient:  ambulance_location  (live ETA)
Flask broadcasts → hospital: ambulance_location  (map update)

── NEW ──────────────────────────────────────────────────────────
Doctor enters vitals on /ambulance
        ↓
ML engine scores all hospitals → returns ranked list
        ↓
Doctor taps Dispatch
        ↓
Flask emits → hospital: ambulance_vitals_update  (vitals + ETA)
```

---

## 📸 Screenshots

| Patient App | Driver Tablet | Hospital Dashboard | Doctor Panel |
|-------------|---------------|-------------------|--------------|
| SOS → Hospital Picker → Live Tracking | Live map + patient info | Pre-alert + prep checklist + zone stats | Vitals entry → ML hospital ranking → dispatch |

---

## 👨‍💻 Developer

**Rudra Narayan**
- GitHub → [amrutanshpanigrahi](https://github.com/amrutanshpanigrahi)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
