from app.db.sqlserver import buscar_pessoa_por_telefone
from app.core.phone import candidate_phones_for_lookup, normalize_phone

def testar_busca_por_telefone(raw_telefone: str) -> None:
    print("\n=== TESTE BUSCA POR TELEFONE (LEGADO) ===")
    print("Telefone informado:", raw_telefone)

    norm = normalize_phone(raw_telefone)
    print("Normalizado:", norm)

    candidates = candidate_phones_for_lookup(raw_telefone)
    print("Candidatos para lookup:", candidates)

    row = buscar_pessoa_por_telefone(raw_telefone)

    if not row:
        print("RESULTADO: NÃO ENCONTRADO ❌")
        return

    # Ordem do SELECT (ajuste se seu SELECT mudar):
    # pessoa.nome, pessoa.cpf, pessoa.datanascimento
    print("RESULTADO: ENCONTRADO ✅")
    print("Nome:", row[0])
    print("CPF:", row[1])
    print("Data nascimento:", row[2])

if __name__ == "__main__":
    # Troque aqui pelo telefone que você quer testar:
    testar_busca_por_telefone("(11) 98625-7349")
