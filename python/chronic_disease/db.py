# -*- coding: utf-8 -*-
"""数据库连接工具。"""
from contextlib import contextmanager

import pymysql

from .config import DB_CONFIG


def connect(database: str | None = None, autocommit: bool = False, local_infile: bool = False):
    cfg = dict(DB_CONFIG)
    if database:
        cfg["database"] = database
    cfg["autocommit"] = autocommit
    cfg["local_infile"] = local_infile
    return pymysql.connect(**cfg)


@contextmanager
def cursor(database: str | None = None):
    conn = connect(database=database)
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
