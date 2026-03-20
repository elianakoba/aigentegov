import os
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Carregamento do .env
# - Busca o .env na raiz do projeto
# - Funciona localmente, na EC2 e via systemd
# -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # raiz do projeto
ENV_FILE = PROJECT_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # Permite rodar mesmo sem .env (ex.: variáveis injetadas pelo sistema)
    load_dotenv()


class Settings:
    # ===============================
    # AMBIENTE
    # ===============================
    # Valores esperados: local | aws | prod | production
    ENV: str = os.getenv("ENV", "local").lower()

    # ===============================
    # APP
    # ===============================
    APP_NAME: str = os.getenv("APP_NAME", "AiGENTEGOV - SDPD API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

    # ===============================
    # AUTENTICAÇÃO (API KEY)
    # ===============================
    # Usada para proteger endpoints sensíveis (gravação / alteração)
    API_KEY: str = os.getenv("API_KEY", "")

    # ===============================
    # SQL SERVER (LEGADO)
    # ===============================
    SQLSERVER_HOST: str = os.getenv("SQLSERVER_HOST", "")
    SQLSERVER_DB: str = os.getenv("SQLSERVER_DB", "")
    SQLSERVER_USER: str = os.getenv("SQLSERVER_USER", "")
    SQLSERVER_PASSWORD: str = os.getenv("SQLSERVER_PASSWORD", "")
    SQLSERVER_DRIVER: str = os.getenv(
        "SQLSERVER_DRIVER",
        "ODBC Driver 17 for SQL Server"
    )

    # ===============================
    # POSTGRESQL (AGENDA / NOTIFICAÇÕES)
    # ===============================
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "postgres")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    # SSL é EXIGIDO em RDS.
    # Em produção, o default NÃO pode ser disable.
    POSTGRES_SSLMODE: str = os.getenv(
        "POSTGRES_SSLMODE",
        "require" if os.getenv("ENV", "local").lower() in {"aws", "prod", "production"} else "disable"
    )

    # ===============================
    # HELPERS (camada DB)
    # ===============================
    @property
    def POSTGRES_DSN(self) -> str:
        """
        DSN padrão para psycopg2.
        """
        return (
            f"host={self.POSTGRES_HOST} "
            f"port={self.POSTGRES_PORT} "
            f"dbname={self.POSTGRES_DB} "
            f"user={self.POSTGRES_USER} "
            f"password={self.POSTGRES_PASSWORD} "
            f"sslmode={self.POSTGRES_SSLMODE}"
        )

    @property
    def POSTGRES_URL(self) -> str:
        """
        URL padrão para ORMs (SQLAlchemy, etc).
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ===============================
    # VALIDAÇÃO DE PRODUÇÃO
    # ===============================
    def validate_required(self) -> None:
        """
        Impede subir em AWS/Prod com configuração incompleta
        ou insegura sem perceber.
        """
        if self.ENV in {"aws", "prod", "production"}:
            missing = []

            if not self.POSTGRES_HOST or self.POSTGRES_HOST == "localhost":
                missing.append("POSTGRES_HOST")

            if not self.POSTGRES_DB:
                missing.append("POSTGRES_DB")

            if not self.POSTGRES_USER:
                missing.append("POSTGRES_USER")

            if not self.POSTGRES_PASSWORD:
                missing.append("POSTGRES_PASSWORD")

            if self.POSTGRES_SSLMODE != "require":
                missing.append("POSTGRES_SSLMODE=require (obrigatório em RDS)")

            if not self.API_KEY:
                missing.append("API_KEY (obrigatória para autenticação da API)")

            if missing:
                raise RuntimeError(
                    "Configuração inválida para AWS/Produção. "
                    f"Ajuste as variáveis: {', '.join(missing)}"
                )


settings = Settings()

# Ative esta linha se quiser falhar imediatamente ao subir errado em produção
# settings.validate_required()
