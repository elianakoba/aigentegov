import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "AiGENTEGOV - SDPD API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

    SQLSERVER_HOST: str = os.getenv("SQLSERVER_HOST", "")
    SQLSERVER_DB: str = os.getenv("SQLSERVER_DB", "")
    SQLSERVER_USER: str = os.getenv("SQLSERVER_USER", "")
    SQLSERVER_PASSWORD: str = os.getenv("SQLSERVER_PASSWORD", "")
    SQLSERVER_DRIVER: str = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server")

settings = Settings()
