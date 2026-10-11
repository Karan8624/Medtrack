# MedTrack

Medication, hydration, and prescription adherence tracker with three roles: Patient, Nurse, and Doctor.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Create the MySQL database and load the schema:
   ```
   mysql -u root -p -e "CREATE DATABASE medtrack"
   mysql -u root -p medtrack < db/schema.sql
   ```
3. Make sure MongoDB is running (local install or an Atlas free-tier connection string).
4. Set environment variables for your DB connection (or edit `db/seed_data.py` directly):
   ```
   export MYSQL_HOST=localhost
   export MYSQL_USER=root
   export MYSQL_PASSWORD=yourpassword
   export MYSQL_DB=medtrack
   export MONGO_URI=mongodb://localhost:27017/
   ```
5. Run the seed script to populate both databases with fake data:
   ```
   python db/seed_data.py
   ```

## Project structure

```
medtrack/
├── db/
│   ├── schema.sql        # MySQL schema — the single source of truth for table structure
│   ├── mongo_schema.md   # MongoDB collection shapes + sample aggregation pipelines
│   └── seed_data.py      # Generates fake patients, doctors, nurses, prescriptions, etc.
├── patient/               # Patient-facing Streamlit pages
├── nurse/                 # Nurse-facing Streamlit pages
├── doctor/                # Doctor-facing Streamlit pages
├── shared/                # Shared DB connection helpers, auth, query functions
└── requirements.txt
```

## Task board (pick up whatever's unblocked)

- [x] Lock schema (SQL + MongoDB)
- [x] Seed data generator
- [ ] `shared/db.py` — MySQL + MongoDB connection helpers
- [ ] `shared/auth.py` — login, password check, role-based session
- [ ] Patient: today's reminders view (dose_log + water_log)
- [ ] Patient: log dose taken/missed
- [ ] Patient: water intake logging
- [ ] Patient: symptom journal entry
- [ ] Patient: raise SOS/complaint
- [ ] Nurse: view assigned patients
- [ ] Nurse: SOS/complaint queue (resolve or escalate)
- [ ] Nurse: task list (view/update status)
- [ ] Doctor: prescription form + drug-interaction check
- [ ] Doctor: escalated SOS review + assign task
- [ ] Doctor: patient adherence overview
- [ ] Query: adherence % (7-day, 30-day) per patient
- [ ] Query: refill-due alert (remaining_qty vs. daily usage)
- [ ] Query: auto-mark missed doses past grace period
- [ ] Login page + role routing (main app entrypoint)
- [ ] Testing: invalid inputs, edge cases
- [ ] Final polish + demo rehearsal
