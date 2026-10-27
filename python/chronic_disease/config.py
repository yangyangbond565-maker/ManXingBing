# -*- coding: utf-8 -*-
"""项目配置：数据库、路径、数据规模。所有敏感信息从环境变量读取。"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
GENERATED_DIR = DATA_DIR / "generated"
ADS_DIR = DATA_DIR / "ads"
SYNC_DIR = DATA_DIR / "sync"
REPORT_DIR = PROJECT_ROOT / "reports"
LOG_DIR = PROJECT_ROOT / "logs"

DB_CONFIG = {
    "host": os.getenv("CHRONIC_DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("CHRONIC_DB_PORT", "3306")),
    "user": os.getenv("CHRONIC_DB_USER", "root"),
    "password": os.getenv("CHRONIC_DB_PASSWORD", ""),
    "database": os.getenv("CHRONIC_DB_NAME", "chronic_disease"),
    "charset": "utf8mb4",
    "autocommit": False,
}

HDFS_URI = os.getenv("CHRONIC_HDFS_URI", "hdfs://127.0.0.1:9000")
HDFS_BASE = os.getenv("CHRONIC_HDFS_BASE", "/warehouse/chronic_disease")
HIVE_DB = os.getenv("CHRONIC_HIVE_DB", "chronic_disease_db")
SPARK_MASTER = os.getenv("CHRONIC_SPARK_MASTER", "local[4]")

PATIENT_COUNT = int(os.getenv("CHRONIC_PATIENT_COUNT", "100000"))
RANDOM_SEED = int(os.getenv("CHRONIC_RANDOM_SEED", "20261020"))

TABLES = [
    "patient_info",
    "disease_record",
    "health_checkup",
    "lifestyle",
    "visit_record",
    "medication_record",
    "follow_up",
]


def ensure_dirs() -> None:
    for p in (GENERATED_DIR, ADS_DIR, SYNC_DIR, REPORT_DIR, LOG_DIR):
        p.mkdir(parents=True, exist_ok=True)
