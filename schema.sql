CREATE DATABASE IF NOT EXISTS iern CHARACTER SET utf8mb4;
USE iern;

CREATE TABLE IF NOT EXISTS hospitals (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(200)    NOT NULL,
    address      TEXT,
    city         VARCHAR(100),
    district     VARCHAR(100),
    lat          DECIMAL(9,6)    NOT NULL,
    lng          DECIMAL(9,6)    NOT NULL,
    rating       DECIMAL(3,1)    DEFAULT 3.0,
    beds         INT             DEFAULT 0,
    er_available TINYINT(1)      DEFAULT 1,
    specialty    VARCHAR(150),
    phone        VARCHAR(20),
    type         ENUM('Government','Private') DEFAULT 'Government',
    zone_id      TINYINT         DEFAULT 3,
    zone_name    VARCHAR(100),
    er_wait_min  INT             DEFAULT 10,
    beds_free    INT             DEFAULT 0,
    created_at   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100)   NOT NULL,
    phone         VARCHAR(15)    UNIQUE,
    blood_group   VARCHAR(5),
    allergies     TEXT,
    lat           DECIMAL(9,6),
    lng           DECIMAL(9,6),
    password_hash VARCHAR(200),
    created_at    TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ambulances (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    driver_name  VARCHAR(100),
    vehicle_no   VARCHAR(20),
    phone        VARCHAR(15),
    lat          DECIMAL(9,6),
    lng          DECIMAL(9,6),
    status       ENUM('available','dispatched','busy') DEFAULT 'available',
    updated_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incidents (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    patient_id          INT,
    ambulance_id        INT,
    hospital_id         INT,
    symptom             VARCHAR(200),
    severity            ENUM('low','medium','high') DEFAULT 'medium',
    status              ENUM('called','dispatched','enroute_patient',
                             'arrived_patient','enroute_hospital',
                             'arrived_hospital','handoff') DEFAULT 'called',
    patient_lat         DECIMAL(9,6),
    patient_lng         DECIMAL(9,6),
    ai_reason           TEXT,
    zone_match          VARCHAR(100),
    called_at           TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    dispatched_at       TIMESTAMP   NULL,
    arrived_patient_at  TIMESTAMP   NULL,
    arrived_hospital_at TIMESTAMP   NULL,
    handoff_at          TIMESTAMP   NULL,
    FOREIGN KEY (patient_id)   REFERENCES patients(id),
    FOREIGN KEY (ambulance_id) REFERENCES ambulances(id),
    FOREIGN KEY (hospital_id)  REFERENCES hospitals(id)
);

CREATE TABLE IF NOT EXISTS hospital_alerts (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    incident_id         INT,
    hospital_id         INT,
    eta_min             INT,
    ai_recommendation   TEXT,
    status              ENUM('sent','acknowledged','ready') DEFAULT 'sent',
    sent_at             TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(id),
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
);

CREATE TABLE IF NOT EXISTS zone_clusters (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id   INT UNIQUE,
    zone_id       TINYINT,
    zone_name     VARCHAR(100),
    cluster_score DECIMAL(5,4),
    updated_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
);

INSERT INTO ambulances (driver_name, vehicle_no, phone, lat, lng, status) VALUES
('Rajan Das',     'OD-02-MH-4821', '9861000001', 20.2900, 85.8250, 'available'),
('Suresh Nayak',  'OD-02-MH-4822', '9861000002', 20.3100, 85.8400, 'available'),
('Manoj Patra',   'OD-02-MH-4823', '9861000003', 20.2750, 85.8100, 'available'),
('Bikash Jena',   'OD-02-MH-4824', '9861000004', 20.4600, 85.8800, 'available'),
('Tapas Mohanty', 'OD-02-MH-4825', '9861000005', 21.5000, 83.8700, 'available');
