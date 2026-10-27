# -*- coding: utf-8 -*-
import csv
from pathlib import Path

from chronic_disease.generate import generate


def test_generate_small_dataset():
    out = Path("data/test_generated")
    out.mkdir(parents=True, exist_ok=True)
    manifest = generate(200, seed=42, out_dir=out)
    assert manifest["patient_count"] == 200
    for table, meta in manifest["tables"].items():
        path = out / f"{table}.csv"
        assert path.exists()
        with path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == meta["rows"]
    # 外键一致性：其余 6 张表的 patient_id 必须存在于 patient_info
    with (out / "patient_info.csv").open(encoding="utf-8") as f:
        ids = {r["patient_id"] for r in csv.DictReader(f)}
    for table in ["disease_record", "health_checkup", "lifestyle", "visit_record", "medication_record", "follow_up"]:
        with (out / f"{table}.csv").open(encoding="utf-8") as f:
            assert all(r["patient_id"] in ids for r in csv.DictReader(f)), table
    with (out / "medication_record.csv").open(encoding="utf-8") as f:
        assert all(r["end_date"] >= r["start_date"] for r in csv.DictReader(f))
    with (out / "follow_up.csv").open(encoding="utf-8") as f:
        assert all(r["next_follow_date"] >= r["follow_date"] for r in csv.DictReader(f))