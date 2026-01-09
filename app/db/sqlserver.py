import pyodbc
from typing import Optional

from app.core.config import settings
from app.core.phone import candidate_phones_for_lookup

def get_sqlserver_connection():
    conn_str = (
        f"DRIVER={{{settings.SQLSERVER_DRIVER}}};"
        f"SERVER={settings.SQLSERVER_HOST};"
        f"DATABASE={settings.SQLSERVER_DB};"
        f"UID={settings.SQLSERVER_USER};"
        f"PWD={settings.SQLSERVER_PASSWORD};"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
        "Connection Timeout=10;"
    )
    return pyodbc.connect(conn_str)

def buscar_pessoa_por_telefone(raw_telefone: str):
    """
    Busca pessoa no SQL Server a partir do telefone,
    respeitando o modelo relacional legado (pessoa + contatopessoa).
    """
    candidates = candidate_phones_for_lookup(raw_telefone)

    conn = get_sqlserver_connection()
    cursor = conn.cursor()

    try:
        for telefone in candidates:
            cursor.execute(
                """
                SELECT
                    pessoa.cpf,
                    pessoa.nome,
                    pessoa.datanascimento,
                    pessoa.id_pessoa
                FROM SDPD.dbo.pessoa pessoa
                    INNER JOIN SDPD.dbo.contatopessoa contatopessoa
                    ON pessoa.id_pessoa = contatopessoa.id_pessoa
                WHERE contatopessoa.descContato = ?
                    AND contatopessoa.id_tipocontato <> 6
                """,
                (telefone,)
            )

            row = cursor.fetchone()
            if row:
                return row

        return None
    finally:
        cursor.close()
        conn.close()


def inserir_historico_sdpd(id_pessoa: int, historico: str, tipo_historico: Optional[int] , id_usuario: Optional[int]):
    """
    Insere um registro em HistoricoSDPD usando GETDATE() no banco.
    Retorna (id_historico, data_gravacao).
    """
    conn = get_sqlserver_connection()
    cursor = conn.cursor()

    try:
        # Monta INSERT dinamicamente para respeitar colunas opcionais
        columns = ["Id_Pessoa", "Historico", "Data"]
        values_sql = ["?", "?", "GETDATE()"]
        params = [id_pessoa, historico]

        if tipo_historico is not None:
            columns.append("vet_TipoHistorico")
            values_sql.append("?")
            params.append(tipo_historico)

        if id_usuario is not None:
            columns.append("Id_Usuario")
            values_sql.append("?")
            params.append(id_usuario)

        sql = f"""
        SET NOCOUNT ON;
        INSERT INTO HistoricoSDPD ({", ".join(columns)})
        VALUES ({", ".join(values_sql)});
        SELECT SCOPE_IDENTITY() AS Id_HistoricoSDPD, GETDATE() AS DataGravacao;
        """

        cursor.execute(sql, params)
        row = cursor.fetchone()
        conn.commit()

        id_historico = int(row[0])
        data_gravacao = row[1]
        return id_historico, data_gravacao

    finally:
        cursor.close()
        conn.close()


def listar_historicos_por_pessoa(id_pessoa: int, limit: int = 50):
    """
    Lista os últimos históricos da pessoa (mais recentes primeiro).
    """
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT TOP (?)
                Id_HistoricoSDPD,
                Id_Pessoa,
                Id_Usuario,
                vet_TipoHistorico,
                Historico,
                Data
            FROM HistoricoSDPD
            WHERE Id_Pessoa = ?
            ORDER BY Data DESC
            """,
            (limit, id_pessoa),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
