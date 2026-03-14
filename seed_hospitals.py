"""
seed_hospitals.py
Reads data/odisha_hospitals.csv, runs ML zone classification,
then inserts all 40 hospitals into MySQL hospitals table.

Run once after schema.sql:
    python seed_hospitals.py
"""

import sys
import os
import mysql.connector

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ml"))
from zone_classifier import load_and_preprocess, train_and_assign

# ── MySQL config — change password to yours ──────────────────────
MYSQL_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "root@123",          # ← put your MySQL password here
    "database": "iern"
}


def seed():
    print("Step 1: Running ML zone classification on CSV...")
    df_raw = load_and_preprocess()
    df     = train_and_assign(df_raw)

    print("\nStep 2: Connecting to MySQL...")
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cur  = conn.cursor()

    upsert_sql = """
    INSERT INTO hospitals
        (id, name, address, city, district, lat, lng, rating,
         beds, er_available, specialty, phone, type,
         zone_id, zone_name, beds_free, er_wait_min)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s,
         %s, %s, %s, %s, %s,
         %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        zone_id    = VALUES(zone_id),
        zone_name  = VALUES(zone_name),
        rating     = VALUES(rating),
        beds       = VALUES(beds),
        beds_free  = VALUES(beds_free)
    """

    print("Step 3: Inserting hospitals into MySQL...")
    rows_inserted = 0

    for _, h in df.iterrows():
        cur.execute(upsert_sql, (
            int(h["id"]),
            h["name"],
            h["address"],
            h["city"],
            h["district"],
            float(h["lat"]),
            float(h["lng"]),
            float(h["rating"]),
            int(h["beds"]),
            int(h["er_available"]),
            h["specialty"],
            h["phone"],
            h["type"],
            int(h["zone_id"]),
            h["zone_name"],
            int(int(h["beds"]) * 0.3),   # 30% beds assumed free
            10                            # default ER wait 10 min
        ))
        rows_inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nDone! {rows_inserted} hospitals seeded into MySQL.")
    print("\nZone summary:")
    summary = df.groupby(["zone_id", "zone_name"])["id"].count().rename("hospitals")
    print(summary.to_string())


if __name__ == "__main__":
    seed()