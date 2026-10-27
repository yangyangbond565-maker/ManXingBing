# -*- coding: utf-8 -*-
import requests
import pytest

BASE = "http://127.0.0.1:8080/api"


def get(path):
    try:
        r = requests.get(BASE + path, timeout=15)
    except requests.RequestException as exc:
        pytest.skip(f"后端未启动: {exc}")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    return body["data"]


def test_overview():
    d = get("/dashboard/overview")
    assert d["totalPatients"] == 100000
    assert d["totalDiseaseRecords"] == 165087


def test_profile_and_health():
    assert len(get("/patient-profile")["rows"]) == 33
    h = get("/health-score/overview")
    assert len(h["levels"]) == 5
    assert h["summary"]["totalPatients"] == 100000


def test_patient_page_and_detail():
    page = get("/patients?page=1&size=2")
    assert page["total"] == 100000
    pid = page["records"][0]["patientId"]
    detail = get(f"/patients/{pid}")
    assert detail["patient"]["patientId"] == pid
    assert "diseases" in detail and "healthScore" in detail


def test_trend_and_quality():
    t = get("/trend?grain=year")
    assert t["metrics"]["algorithm"].startswith("最小二乘")
    assert len(t["forecast"]) == 4
    q = get("/data-quality")
    assert q["summary"]["totalIssues"] == 0
