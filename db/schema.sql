-- MedTrack: Relational Schema (MySQL)
-- Run this against a fresh database, e.g.:
--   CREATE DATABASE medtrack;
--   USE medtrack;
--   SOURCE schema.sql;

CREATE TABLE doctors (
    doctor_id       INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    specialization  VARCHAR(100),
    email           VARCHAR(150) UNIQUE,
    password_hash   VARCHAR(255) NOT NULL
);

CREATE TABLE nurses (
    nurse_id        INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(150) UNIQUE,
    password_hash   VARCHAR(255) NOT NULL
);

CREATE TABLE patients (
    patient_id      INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    age             INT,
    gender          VARCHAR(20),
    weight_kg       DECIMAL(5,2),
    email           VARCHAR(150) UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    water_target_ml INT DEFAULT 2000,
    doctor_id       INT,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

-- Each patient has exactly one assigned nurse (case-load model)
CREATE TABLE nurse_assignments (
    assignment_id   INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT NOT NULL UNIQUE,
    nurse_id        INT NOT NULL,
    assigned_date   DATE NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id)
);

CREATE TABLE medicines (
    medicine_id     INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    unit            VARCHAR(20) DEFAULT 'tablet'
);

-- Reference table of known interaction pairs (seeded with real, cited data)
CREATE TABLE drug_interactions (
    interaction_id  INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id_a   INT NOT NULL,
    medicine_id_b   INT NOT NULL,
    severity        ENUM('Moderate', 'Severe') NOT NULL,
    description     VARCHAR(255),
    FOREIGN KEY (medicine_id_a) REFERENCES medicines(medicine_id),
    FOREIGN KEY (medicine_id_b) REFERENCES medicines(medicine_id)
);

CREATE TABLE prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT NOT NULL,
    doctor_id       INT NOT NULL,
    medicine_id     INT NOT NULL,
    dosage          VARCHAR(50) NOT NULL,       -- e.g. "500mg"
    frequency       INT NOT NULL,               -- doses per day
    quantity        INT NOT NULL,               -- total units dispensed
    remaining_qty   INT NOT NULL,               -- manually confirmable stock
    start_date      DATE NOT NULL,
    end_date        DATE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)
);

CREATE TABLE dose_log (
    dose_id         INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    scheduled_time  DATETIME NOT NULL,
    actual_time     DATETIME,
    status          ENUM('Pending', 'Taken', 'Missed') DEFAULT 'Pending',
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id)
);

-- SOS / complaint lifecycle
CREATE TABLE sos_complaints (
    sos_id          INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT NOT NULL,
    nurse_id        INT NOT NULL,
    doctor_id       INT NOT NULL,
    description     TEXT NOT NULL,
    severity        ENUM('Low', 'Medium', 'Urgent') NOT NULL,      -- set by patient, revisable by nurse
    status          ENUM('Raised', 'Under Nurse Review', 'Self-Resolved',
                          'Escalated', 'Doctor Reviewed',
                          'Resolved', 'Resolved (In-Person Required)') DEFAULT 'Raised',
    raised_at       DATETIME NOT NULL,
    nurse_reviewed_at DATETIME,
    escalated_at    DATETIME,
    doctor_reviewed_at DATETIME,
    resolved_at     DATETIME,
    resolution_notes TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

-- Tasks assigned by a doctor to a nurse (delivery, injection, procedure)
CREATE TABLE tasks (
    task_id         INT AUTO_INCREMENT PRIMARY KEY,
    sos_id          INT,                        -- nullable: a task can exist without an SOS
    patient_id      INT NOT NULL,
    nurse_id        INT NOT NULL,
    assigned_by_doctor_id INT NOT NULL,
    task_type       ENUM('Delivery', 'Injection', 'Procedure', 'Other') NOT NULL,
    status          ENUM('Pending', 'In Progress', 'Completed') DEFAULT 'Pending',
    notes           TEXT,
    created_at      DATETIME NOT NULL,
    completed_at    DATETIME,
    FOREIGN KEY (sos_id) REFERENCES sos_complaints(sos_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id),
    FOREIGN KEY (assigned_by_doctor_id) REFERENCES doctors(doctor_id)
);
