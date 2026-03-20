# app/db/session.py
from __future__ import annotations

from contextlib import contextmanager
import psycopg2

from app.core.config import settings


@contextmanager
def get_db():
    """
    Abre conexão com PostgreSQL usando o DSN do settings (psycopg2).
    Uso:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    """
    conn = None
    try:
        conn = psycopg2.connect(settings.POSTGRES_DSN)
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            conn.close()