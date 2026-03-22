import os
import pyodbc


def get_sqlserver_connection():
    driver = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server")
    host = os.getenv("SQLSERVER_HOST")
    db = os.getenv("SQLSERVER_DB")
    user = os.getenv("SQLSERVER_USER")
    password = os.getenv("SQLSERVER_PASSWORD")

    missing = [k for k, v in {
        "SQLSERVER_HOST": host,
        "SQLSERVER_DB": db,
        "SQLSERVER_USER": user,
        "SQLSERVER_PASSWORD": password,
    }.items() if not v]

    if missing:
        raise RuntimeError(f"Variáveis SQL Server ausentes no .env: {', '.join(missing)}")

    conn_str = (
        f"Driver={{{driver}}};"
        f"Server={host};"
        f"Database={db};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
    )

    return pyodbc.connect(conn_str)