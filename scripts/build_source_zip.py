# -*- coding: utf-8 -*-
"""生成可提交的源代码压缩包，排除依赖、虚拟磁盘、密码和大数据文件。"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DIST.mkdir(parents=True, exist_ok=True)
OUT = DIST / "社区慢性病大数据分析系统-源代码.zip"

EXCLUDE_DIRS = {
    ".git", ".tools", ".tmp", ".hadoop", ".npm-cache", ".spark-warehouse",
    "node_modules", "target", "dist", "__pycache__", ".pytest_cache", "metastore_db", "backup",
    "data/warehouse", "data/sync", "data/test_smoke", "data/test_generated",
}
EXCLUDE_SUFFIXES = {".pyc"}
INCLUDE_LOG = {
    "logs/spark_run.log", "logs/spark_hdfs_run.log", "logs/hdfs_verification.log",
    "logs/webhdfs_sync.log", "logs/hive_counts.log", "logs/hive_ads_queries.log",
    "logs/hive_ddl.log", "logs/hive_ads.log", "logs/hive_query.log",
    "logs/spark_hdfs_smoke.log", "logs/hdfs_ads_check.log", "logs/hive_config_hdfs.log", "logs/hdfs_ods_sizes.log",
    "logs/sqoop_check.log", "logs/sqoop_install.log", "logs/sqoop_jdbc.log",
    "logs/sqoop_eval.log", "logs/sqoop_import.log", "logs/sqoop_content_check.log", "logs/sqoop_install.log", "logs/sqoop_jdbc.log",
    "logs/sqoop_eval.log", "logs/sqoop_import.log", "logs/sqoop_content_check.log",
}
SKIP_FILES = {
    "backend/.env.local", "backend/.env", ".env", ".env.local",
}


def allowed(rel: Path) -> bool:
    s = rel.as_posix()
    if s in SKIP_FILES:
        return False
    parts = set(rel.parts)
    if parts & EXCLUDE_DIRS:
        return False
    if any(s.startswith(d + "/") for d in EXCLUDE_DIRS):
        return False
    if s.startswith("data/generated/") and rel.name != "manifest.json":
        return False
    if s.startswith("pytest-cache-files-"):
        return False
    if s.endswith(".log") and s not in INCLUDE_LOG:
        return False
    if rel.suffix in EXCLUDE_SUFFIXES:
        return False
    return True


files = []
for p in ROOT.rglob("*"):
    if not p.is_file():
        continue
    rel = p.relative_to(ROOT)
    if allowed(rel):
        files.append((p, rel))

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p, rel in sorted(files, key=lambda x: x[1].as_posix()):
        z.write(p, rel.as_posix())

h = hashlib.sha256(OUT.read_bytes()).hexdigest()
(DIST / "SHA256SUMS.txt").write_text(f"{h}  {OUT.name}\n", encoding="utf-8")
print("zip", OUT)
print("files", len(files), "size_mb", round(OUT.stat().st_size / 1024 / 1024, 2))
print("sha256", h)