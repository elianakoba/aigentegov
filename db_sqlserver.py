import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def get_sqlserver_connection():
    host = os.getenv("SQLSERVER_HOST")
    db = os.getenv("SQLSERVER_DB")
    user = os.getenv("SQLSERVER_USER")
    password = os.getenv("SQLSERVER_PASSWORD")
    driver = os.getenv("SQLSERVER_DRIVER")

    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={'200.160.203.246\DESENVOLVIMENTO'};"
        f"DATABASE={'SDPD'};"
        f"UID={'opSDPD'};"
        f"PWD={'sdpdpmb@5778'};"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(conn_str)