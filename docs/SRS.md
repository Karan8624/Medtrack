# MedTrack — Medication, Hydration & Prescription Adherence Tracker

## Project Pitch

Missed doses and forgotten water intake are two of the simplest, most preventable causes of poor health outcomes — especially for elderly patients, people managing chronic conditions, or anyone juggling multiple prescriptions with different timings. MedTrack is a Python-based data-driven application that turns a doctor's prescription into a structured, trackable daily routine: it reminds patients when to take each medicine, when to drink water, flags conflicts between prescribed drugs, warns before a patient runs out of medicine, and gives doctors a simple adherence view across their patients — all backed by a relational database for structured records and a NoSQL store for flexible, free-form health logs.

Beyond the doctor and patient roles, MedTrack introduces a **Nurse** role as a first-response layer: each patient has a permanently assigned nurse, and any SOS or complaint a patient raises reaches both the nurse and the doctor at once. Since doctors don't have time to review every complaint, the nurse triages first — handling routine issues (medicine delivery, a scheduled shot, a simple procedure) directly, and escalating only what genuinely needs a doctor's attention. This keeps doctors focused on the cases that matter while patients still get a fast response.

The project is built and evaluated entirely on synthetic (fake) data, so it avoids the real-world complexity of clinical deployment (consent, compliance, integration with hospital systems) while still exercising every skill the DCDS Lab rubric evaluates: application design, Python implementation, SQL + NoSQL integration, advanced querying, code quality, and testing/validation/security.

**SDG Alignment (2 selected):**
- **SDG 3 — Good Health and Well-being:** directly supports medication adherence and preventive self-care.
- **SDG 10 — Reduced Inequalities:** designed with elderly and low-literacy patients in mind, who are disproportionately affected by missed doses and complex prescription schedules.

---

## Software Requirements Specification (SRS)

### 1. Introduction

**1.1 Purpose**
This document specifies the requirements for MedTrack, a desktop/web-based Python application that tracks patient prescriptions, medicine and hydration reminders, adherence trends, and flags safety concerns (drug interactions, low stock). It is intended for academic evaluation under the DCDS Lab ESE miniproject.

**1.2 Scope**
MedTrack manages patients, doctors, medicines, and prescriptions in a relational database, and stores flexible health-journal data (symptoms, hydration logs, notes) in a NoSQL document store. It provides two user roles — patient and doctor — and generates reminders, adherence statistics, and safety alerts from synthetic data.

**1.3 Intended Users**
Patients (self-tracking medicine/water intake), nurses (first-response triage and task execution), and doctors (prescribing and case oversight). All users and data in this project are simulated for demonstration purposes.

**1.4 Definitions & Acronyms**

| Term | Meaning |
|---|---|
| SOS/Complaint | A patient-initiated report of a health concern or medicine shortage |
| Case-load | The fixed set of patients permanently assigned to one nurse |
| Adherence rate | Percentage of scheduled doses actually taken, over a given window |
| Grace period | Time allowed after a scheduled dose before it's auto-marked Missed |
| CRUD | Create, Read, Update, Delete |
| ESE | End Semester Exam / Evaluation (the DCDS Lab miniproject assessment) |

### 2. Overall Description

**2.1 Product Perspective**
Standalone application; not integrated with any real hospital or pharmacy system. Uses MySQL/PostgreSQL for structured data and MongoDB for unstructured/semi-structured data.

**2.2 User Roles**
- *Patient:* views today's reminders, logs doses as taken/missed, logs water intake, writes symptom/side-effect notes, views own adherence trend, and raises an SOS/complaint when something feels wrong or when they've run out of medicine.
- *Nurse:* permanently assigned to a fixed set of patients (case-load). Receives every SOS/complaint raised by their assigned patients at the same time as the doctor. Triages each case: resolves it directly if routine (delivering medicine, administering a scheduled shot, performing a simple procedure at the patient's location), or flags/escalates it to the doctor if it needs medical judgment. Marks assigned tasks and procedures as completed, with notes.
- *Doctor:* creates/updates prescriptions for their patients, assigns a nurse to each patient, receives drug-interaction warnings when prescribing, and sees only the SOS/complaint cases a nurse has escalated (not the full raw stream) — keeping their attention on what actually needs it. On reviewing an escalated case, the doctor can either assign a task back to the nurse (e.g., "administer this injection," "deliver this medicine") or request the patient come in for an in-person visit.

**2.3 Assumptions & Constraints**
Data is synthetic. Reminders are simulated within the app (e.g., a "due now / overdue" queue) rather than sent via real push notification/SMS. No real PHI (protected health information) is used or stored.

**2.4 Use Case Summary**

| Role | Use Cases |
|---|---|
| Patient | View today's reminders · Log dose taken/missed · Log water intake · Add symptom journal entry · Raise SOS/complaint · View own adherence trend |
| Nurse | View assigned patients (case-load) · Review incoming SOS/complaint · Self-resolve or escalate a case · View/update assigned tasks |
| Doctor | Create/update prescription (with interaction check) · Assign nurse to patient · View escalated SOS cases · Assign task to nurse or request in-person visit · View patient adherence overview |

### 3. Functional Requirements

| ID | Requirement |
|---|---|
| FR1 | System shall allow creation and management of patients, doctors, and medicines. |
| FR2 | System shall allow a doctor to create a prescription (medicine, dosage, frequency, start/end date) for a patient. |
| FR3 | System shall generate a daily reminder schedule from active prescriptions (medicine times) and water-intake targets. |
| FR4 | System shall let a patient mark a scheduled dose as Taken or Missed, with timestamp. |
| FR5 | System shall auto-mark a dose as Missed if not logged within a configurable grace period after the scheduled time. |
| FR6 | System shall let a patient log water intake entries (timestamp, amount) at any time. |
| FR7 | System shall let a patient add free-text symptom/side-effect journal entries, optionally tagged with severity/mood. |
| FR8 | System shall compute and display adherence rate (%) per patient over 7-day and 30-day windows. |
| FR9 | System shall flag a potential drug interaction when a new prescription conflicts with an existing active one, using a reference interaction table. |
| FR10 | System shall compute remaining medicine quantity from dosage × frequency and flag a refill-due alert before supply runs out. |
| FR11 | System shall let a doctor view all patients under their care with adherence rate and flag those below an adherence threshold. |
| FR12 | System shall support basic authentication distinguishing patient and doctor roles, with each seeing only their own authorized data. |
| FR13 | System shall validate all inputs (dosage values, dates, quantities) and handle invalid entries gracefully with clear error messages. |
| FR14 | System shall allow a doctor to assign exactly one nurse to each patient (case-load assignment), reassignable if needed. |
| FR15 | System shall allow a patient to raise an SOS/complaint (free-text description, optional severity tag), visible immediately to both their assigned nurse and their doctor. |
| FR16 | System shall let a nurse mark an SOS/complaint as Self-Resolved (with resolution notes) or Escalated to Doctor. |
| FR17 | System shall let a doctor view only escalated SOS/complaint cases by default, with the option to view the full history per patient. |
| FR18 | System shall let a doctor, on reviewing an escalated case, either assign a task to the patient's nurse (medicine delivery, injection/shot, procedure) or mark the case as requiring an in-person visit. |
| FR19 | System shall let a nurse view and update the status of tasks assigned to them (Pending → In Progress → Completed), with completion notes. |
| FR20 | System shall track the full lifecycle timestamps of an SOS/complaint (raised, reviewed by nurse, escalated/resolved, doctor action, completed) to support turnaround-time reporting. |

### 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR1 | Application shall present a clear dashboard view (reminders due, adherence trend, refill alerts) rather than raw tables only. |
| NFR2 | Code shall be modular (separate modules for database access, business logic, and UI) with meaningful naming and comments. |
| NFR3 | All database operations shall use parameterized queries to prevent injection. |
| NFR4 | System shall handle missing/malformed data (e.g., a prescription with no end date) without crashing. |
| NFR5 | Response time for dashboard load and query operations shall remain interactive (under ~2 seconds) on the demo dataset size (~20-30 patients). |

### 5. Technology Stack

**Frontend / Application Layer:** Python, using Streamlit (rapid dashboard-style UI for three roles) — alternatively Tkinter or Flask if a more traditional desktop/web split is preferred by the team.

**Relational Database:** MySQL (or PostgreSQL) — chosen for strong support of joins, nested queries, grouping/aggregation, stored procedures, and referential integrity, all of which the structured entities (patients, doctors, nurses, prescriptions, dose logs, drug interactions, SOS/complaints, tasks) require.

**NoSQL Database:** MongoDB — chosen for its document model and native aggregation pipeline, suited to variable-shape data (symptom journal entries, water intake logs) that doesn't need a fixed schema or foreign-key constraints.

**Connectivity Libraries:** `mysql-connector-python` (or `psycopg2` for PostgreSQL) for the relational layer; `pymongo` for MongoDB.

**Supporting Libraries:** `pandas` (data handling/reporting), `Faker` (synthetic data generation for demo purposes), `bcrypt` or similar (password hashing for basic role-based authentication).

### 5a. Drug Interaction Reference Data

The `drug_interactions` table is seeded with real, well-documented, non-proprietary drug interactions drawn from established clinical pharmacology references (e.g., American Academy of Family Physicians clinical reviews), rather than invented pairs — since this is the one part of the project where medical accuracy matters even in a fake-data demo.

| Medicine A | Medicine B | Interaction / Risk | Severity |
|---|---|---|---|
| Warfarin | Aspirin / Ibuprofen | Increased bleeding risk | Severe |
| Warfarin | Amoxicillin | Enhanced anticoagulant effect | Moderate |
| Lisinopril (ACE inhibitor) | Spironolactone (potassium-sparing diuretic) | Hyperkalemia | Severe |
| Simvastatin (statin) | Erythromycin (macrolide) | Increased risk of muscle toxicity | Severe |
| Phenelzine (MAOI) | Fluoxetine (SSRI) | Serotonin syndrome | Severe |
| Metformin | Iodinated contrast agents | Risk of lactic acidosis | Moderate |
| Digoxin | Furosemide | Electrolyte imbalance increasing digoxin toxicity | Moderate |
| Sildenafil | Nitroglycerin (nitrate) | Severe hypotension | Severe |
| Methotrexate | NSAIDs (e.g., Ibuprofen) | Increased methotrexate toxicity | Moderate |
| Diazepam (benzodiazepine) | Morphine (opioid) | Respiratory depression risk | Severe |

*Source basis: standard clinical pharmacology references (e.g., AAFP, "Clinically Relevant Drug-Drug Interactions in Primary Care").*

### 6. Data Design (Summary)

**Relational (SQL) — structured, constraint-heavy data:**
`patients`, `doctors`, `nurses`, `medicines`, `prescriptions` (patient_id, doctor_id, medicine_id, dosage, frequency, start_date, end_date, quantity), `dose_log` (prescription_id, scheduled_time, actual_time, status), `drug_interactions` (medicine_id_a, medicine_id_b, severity), `nurse_assignments` (patient_id, nurse_id, assigned_date), `sos_complaints` (patient_id, nurse_id, doctor_id, description, severity, status: Raised/Under Nurse Review/Escalated/Self-Resolved/Doctor Reviewed/Resolved, timestamps for each stage), `tasks` (sos_id or standalone, nurse_id, patient_id, type: Delivery/Injection/Procedure, assigned_by_doctor_id, status: Pending/In Progress/Completed, notes).

**Document (MongoDB) — flexible, variable-shape data:**
`symptom_journal` (patient_id, timestamp, free-text note, optional tags/severity/mood — shape varies per entry), `water_log` (patient_id, timestamp, amount_ml).

The split is intentional: relational data has fixed structure and referential integrity needs (a prescription must reference a real patient/doctor/medicine); journal and hydration entries vary in shape per record and don't benefit from a rigid schema.

### 7. Sample Advanced Queries (illustrative)

- **Join + aggregation:** adherence rate per patient over last 7 days (dose_log joined with prescriptions, grouped by patient, taken/total).
- **Nested query:** medicines due in the next hour across all active patients.
- **Stored procedure/trigger:** auto-mark a dose_log row as "Missed" if no actual_time is recorded within the grace period.
- **Join for safety:** check new prescription's medicine against a patient's other active prescriptions via `drug_interactions`.
- **MongoDB aggregation pipeline:** average daily water intake per patient over the last 30 days; symptom-tag frequency count.
- **Join across patient/nurse/doctor/sos_complaints:** average time from SOS raised to nurse review, and from escalation to doctor action, grouped by severity.
- **Aggregation:** count of self-resolved vs. escalated complaints per nurse (nurse workload/effectiveness view).
- **Nested query:** patients whose assigned nurse currently has more than N pending tasks (workload-balancing check).
- **Join for doctor dashboard:** escalated SOS cases still awaiting doctor action, joined with patient and nurse details, ordered by wait time.

### 7a. SOS / Complaint & Task Workflow (Summary)

1. Patient raises an SOS/complaint (e.g., "ran out of insulin," "feeling dizzy") → status **Raised** → visible instantly to both assigned nurse and doctor.
2. Nurse reviews it → status **Under Nurse Review**.
3. Nurse decides:
   - Routine issue → nurse resolves directly (e.g., schedules a delivery or visit themselves) → status **Self-Resolved**, with notes.
   - Needs medical judgment → nurse flags it → status **Escalated to Doctor**.
4. Doctor reviews escalated case → status **Doctor Reviewed**, and chooses one of:
   - Assign a task to the patient's nurse (medicine delivery, injection/shot, minor procedure) → creates a **task** → nurse executes and marks **Completed**.
   - Request the patient come in for an in-person visit → status **Resolved (In-Person Required)**.
5. All stage timestamps are logged, enabling turnaround-time and workload reporting.

### 8. Out of Scope

Real push notifications/SMS, integration with real pharmacy or EHR systems, real patient data or consent workflows, mobile app packaging (a web/desktop demo is sufficient for this project's scope).

### 9. Team & Module Ownership

The project is divided into four independent modules so all four members can work in parallel without blocking each other, after the schema (Section 6) is agreed on as a team.

| Member | Module | Owns |
|---|---|---|
| Member 1 | Environment, Database Access & Auth | MySQL + MongoDB setup shared by the team; `shared/db.py` connection helpers; `shared/auth.py` login + role-based session; running and validating `seed_data.py` |
| Member 2 | Patient Interface | Reminder queue, dose logging, water intake logging, symptom journal (MongoDB), SOS/complaint form |
| Member 3 | Nurse Interface | Assigned-patient view, SOS/complaint triage queue (self-resolve/escalate), task list (status updates) |
| Member 4 | Doctor Interface & Core Queries | Prescription form with drug-interaction check, escalated-case review + task assignment, adherence overview, adherence % / refill-due / auto-missed-dose queries |

Each module depends on Member 1's `db.py`/`auth.py` existing, but can be scaffolded against dummy data in parallel and wired in once that's ready. Because the team is working dynamically rather than in fixed lanes, any member can pick up any unassigned task on the checklist in `README.md` once their own module reaches a stable point.

### 10. Deployment Considerations & Future Work

This project is designed with production deployment in mind — clean schema, real validation, role separation — but is not submitted as demo-launch-ready for real patients. Before any real-world use, it would additionally require: hardened authentication (proper session management, not just password hashing), legal/compliance review for health data handling (e.g., India's DPDP Act), and a genuine incident-response protocol for the SOS feature, since a real deployment implies someone is actively monitoring alerts in real time. These are intentionally out of scope for the academic build but worth naming in the report to show awareness of the gap between a class project and a real clinical tool.

### 11. Suggested Timeline (4-week window)

| Week | Focus |
|---|---|
| 1 | Finalize schema as a team; Member 1 sets up shared DB access/auth; seed data validated by everyone |
| 2 | Core feature build across all three interfaces, in parallel |
| 3 | Integration (login/role routing tying interfaces together) + advanced query layer wired into dashboards |
| 4 | Testing, edge-case handling, UI polish, and a full demo rehearsal (patient → nurse → doctor walkthrough) |
