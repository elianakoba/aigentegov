import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings


def get_connection():
    """
    Cria e retorna uma conexão com o PostgreSQL.
    Usa RealDictCursor para retornar dicionários.
    """
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        sslmode=settings.POSTGRES_SSLMODE,
        cursor_factory=RealDictCursor,
    )
