# MedTrack — MongoDB Schema

Database name: `medtrack`

## Collection: `symptom_journal`

Free-text/flexible entries a patient logs about how they're feeling. Shape varies per entry — this is why it lives in MongoDB rather than SQL.

```json
{
  "_id": ObjectId(),
  "patient_id": 12,
  "timestamp": "2026-09-22T18:30:00Z",
  "note": "Felt dizzy after the 2pm dose, mild headache",
  "tags": ["dizziness", "headache"],
  "severity": "mild",
  "mood": "tired"
}
```

Notes:
- `patient_id` links back to the SQL `patients` table (application-level join, not a DB-enforced FK).
- `tags`, `severity`, `mood` are optional — not every entry will have all fields, which is the point.

## Collection: `water_log`

```json
{
  "_id": ObjectId(),
  "patient_id": 12,
  "timestamp": "2026-09-22T09:15:00Z",
  "amount_ml": 250
}
```

Notes:
- Simple, high-volume, append-only log. Daily/weekly totals are computed via aggregation pipelines, not stored redundantly.

## Sample aggregation pipelines

**Average daily water intake per patient (last 30 days):**
```python
db.water_log.aggregate([
    {"$match": {"timestamp": {"$gte": thirty_days_ago}}},
    {"$group": {
        "_id": {
            "patient_id": "$patient_id",
            "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
        },
        "daily_total_ml": {"$sum": "$amount_ml"}
    }},
    {"$group": {
        "_id": "$_id.patient_id",
        "avg_daily_ml": {"$avg": "$daily_total_ml"}
    }}
])
```

**Symptom tag frequency (across all patients):**
```python
db.symptom_journal.aggregate([
    {"$unwind": "$tags"},
    {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
])
```
