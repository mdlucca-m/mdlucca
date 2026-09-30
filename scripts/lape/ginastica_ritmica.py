"""Ginástica rítmica: uma aba PRIVADA.

Pedido explícito do Mateus: "crie uma aba que sómente a Maria Helena, eu
e o Vilarino temos acesso", para acompanhar estudos sobre variáveis
psicológicas na ginástica rítmica.

Não reaproveita a tabela `articles`: ela é lida por qualquer integrante
na tela "Artigos", e dar privacidade por linha ali exigiria mexer numa
tela grande e muito usada só para esconder um punhado de registros dela.
Uma tabela dedicada, pequena e isolada resolve sem esse risco.

O acesso é uma LISTA (`ginastica_ritmica_acesso`), não três nomes fixos
no código: quem concede e quem revoga é a própria coordenação, escolhendo
entre os integrantes já cadastrados -- assim ninguém aqui precisa
adivinhar a grafia exata do nome de uma pessoa. `admin` sempre vê: já tem
o banco inteiro na mão, então esconder esta tabela dele não protege nada
e só atrapalha suporte.
"""
from __future__ import annotations

from typing import Any

from .db import Database
from .util import clean_text, to_float, to_int


def tem_acesso(db: Database, member_id: int | None, user_role: str | None = None) -> bool:
    if user_role == "admin":
        return True
    if not member_id:
        return False
    return bool(db.scalar(
        "SELECT 1 FROM ginastica_ritmica_acesso WHERE member_id = ?", (member_id,)))


def conceder(db: Database, member_id: int, concedido_por: int | None) -> None:
    db.execute(
        "INSERT INTO ginastica_ritmica_acesso (member_id, concedido_por) VALUES (?, ?)"
        " ON CONFLICT (member_id) DO NOTHING", (member_id, concedido_por))
    db.conn.commit()


def revogar(db: Database, member_id: int) -> None:
    db.execute("DELETE FROM ginastica_ritmica_acesso WHERE member_id = ?", (member_id,))
    db.conn.commit()


def quem_tem_acesso(db: Database) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT m.id, m.full_name, a.concedido_em"
        "  FROM ginastica_ritmica_acesso a JOIN members m ON m.id = a.member_id"
        " ORDER BY m.full_name")


def listar_estudos(db: Database, limite: int = 400) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT * FROM ginastica_ritmica_estudos"
        " ORDER BY ano_publicacao DESC, titulo LIMIT ?", (limite,))


def gravar_estudo(db: Database, criado_por: int | None, registro_id: Any = None,
                  titulo: Any = None, autores: Any = None, ano_publicacao: Any = None,
                  study_type: Any = None, qualis: Any = None, fator_impacto: Any = None,
                  observacoes: Any = None) -> int:
    """Cadastra um estudo novo, ou atualiza um existente quando `registro_id`
    vem preenchido -- o mesmo contrato do formulário de Artigos: todo campo
    viaja sempre, e o que a pessoa apagou na tela apaga no banco."""
    campos = {
        "titulo": clean_text(titulo), "autores": clean_text(autores),
        "ano_publicacao": to_int(ano_publicacao), "study_type": clean_text(study_type),
        "qualis": clean_text(qualis), "fator_impacto": to_float(fator_impacto),
        "observacoes": clean_text(observacoes),
    }
    estudo_id = to_int(registro_id)
    if estudo_id:
        db.execute(
            "UPDATE ginastica_ritmica_estudos SET titulo = ?, autores = ?,"
            " ano_publicacao = ?, study_type = ?, qualis = ?, fator_impacto = ?,"
            " observacoes = ?, atualizado_em = datetime('now') WHERE id = ?",
            (*campos.values(), estudo_id))
        db.conn.commit()
        return estudo_id
    if not campos["titulo"]:
        raise ValueError("título é obrigatório")
    novo_id = db.execute(
        "INSERT INTO ginastica_ritmica_estudos"
        " (titulo, autores, ano_publicacao, study_type, qualis, fator_impacto,"
        "  observacoes, criado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (*campos.values(), criado_por)).lastrowid
    db.conn.commit()
    return novo_id


def excluir_estudo(db: Database, estudo_id: int) -> bool:
    cursor = db.execute("DELETE FROM ginastica_ritmica_estudos WHERE id = ?", (estudo_id,))
    if cursor.rowcount:
        db.conn.commit()
    return bool(cursor.rowcount)
