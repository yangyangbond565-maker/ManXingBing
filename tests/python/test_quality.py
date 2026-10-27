# -*- coding: utf-8 -*-
from chronic_disease.quality_check import build_report


def test_full_database_quality():
    report = build_report()
    assert report["patient_count"] == 100000
    assert report["patient_count_ok"] is True
    assert report["critical_issue_count"] == 0
    assert report["status"] == "PASS"
    assert report["total_rows_all_tables"] >= 2_000_000
