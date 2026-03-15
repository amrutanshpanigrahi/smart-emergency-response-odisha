# 🚑 Smart Emergency Response Odisha

An intelligent ambulance dispatch and hospital routing system for Odisha, built with Python, Flask, MySQL, Machine Learning (K-Means), and real-time WebSocket communication.

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

## 🤖 AI Recommendation Engine

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
| Machine Learning | scikit-learn (K-Means), pandas, numpy |
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
│       └── ml_api.py
├── ml/
│   └── zone_classifier.py
├── data/
│   └── odisha_hospitals.csv
├── templates/
│   ├── patient.html
│   ├── driver.html
│   ├── hospital.html
│   └── zone_map.html
├── schema.sql
├── seed_hospitals.py
├── run.py
└── requirements.txt
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/RudraNarayan2005/smart-emergency-response-odisha.git
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

---

## 📡 Real-Time Flow
```
Patient confirms hospital
        ↓
Flask emits → driver:   new_incident   (patient + hospital info)
Flask emits → hospital: hospital_alert (patient + ETA + AI note)
        ↓
Driver pushes GPS every 5s
        ↓
Flask broadcasts → patient:  ambulance_location (live ETA)
Flask broadcasts → hospital: ambulance_location (map update)
```

---

## 📸 Screenshots

| Patient App | Driver Tablet | Hospital Dashboard |
|-------------|---------------|-------------------|
| SOS → Hospital Picker → Live Tracking | Live map + patient info | Pre-alert + prep checklist + zone stats |

---

## 👨‍💻 Developer

**Rudra Narayan**
- GitHub → [amrutanshpanigrahi](https://github.com/amrutanshpanigrahi)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
