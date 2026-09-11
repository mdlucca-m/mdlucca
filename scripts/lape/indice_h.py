"""O indice h de cada pesquisador: quem declara, quem calcula, quem ganha.

Os numeros estavam errados na tela -- Guilherme aparecia com 17 onde o
certo e 16 -- e a causa nao era um erro de conta. Era nao haver, no
sistema, nenhum lugar onde o numero certo pudesse ser dito. Havia duas
estimativas brigando pela mesma coluna:

  `banco_lape`      calcula o h com os artigos cadastrados AQUI. Ignora a
                    carreira anterior ao laboratorio, entao sai baixo.
  `openalex_author` copia o h do perfil publico do OpenAlex. Traz a
                    carreira inteira, mas o OpenAlex junta homonimo,
                    conta preprint e duplicata, e sai alto.

Nenhuma das duas e o numero que a pessoa poe no Lattes, e as duas se
sobrescreviam: bastava rodar o rastreador para o valor conferido a mao
desaparecer, sem aviso e sem registro.

Agora ha uma terceira coluna, `h_index_declarado`, que e a conferida por
gente e que nenhum recalculo encosta. As estimativas continuam sendo
calculadas e continuam visiveis ao lado -- divergencia entre o declarado
e o calculado e informacao, e escondi-la e que seria errado.

Duas coisas que a declaracao carrega, e sem as quais ela nao serve:

  a BASE  -- 16 na Scopus e 21 no Google Academico sao os dois certos, de
             coisas diferentes. Indice h sem fonte nao se confere.
  a DATA  -- o indice h so sobe. Um numero declarado ha tres anos nao esta
             errado, esta velho, e a tela precisa dizer isso em vez de
             apresenta-lo como se fosse de hoje.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .db import Database
from .util import author_key

# Depois de quantos meses a declaracao passa a ser mostrada como "a
# conferir". Nao apaga e nao recalcula: so avisa. Um ano e o intervalo em
# que um pesquisador ativo costuma ver o proprio h mudar.
VALIDADE_MESES = 12

BASES = ("Scopus", "Web of Science", "Google Acadêmico", "Lattes")

# Os indices que a coordenacao declarou, com a data em que os declarou.
# Entram so onde ainda nao ha declaracao nenhuma -- depois disso, quem
# manda e o que for gravado pela tela. Ficam escritos aqui pelo mesmo
# motivo das fusoes declaradas em duplicatas.py: sao decisoes de quem
# conhece a equipe, e redigitar a cada instalacao e perde-las.
#
# (nome, indice, base, data)
INDICES_DECLARADOS: tuple[tuple[str, int, str, str], ...] = (
    ("Guilherme", 16, "Scopus", "2026-09-11"),
    ("Pierluigi", 28, "Scopus", "2026-09-11"),
    ("Darlan", 11, "Scopus", "2026-09-11"),
)


def declarar(db: Database, member_id: int, valor: int | None,
             base: str | None = None, por: str | None = None,
             em: str | None = None) -> dict[str, Any]:
    """Grava o indice h conferido por gente.

    `valor` None apaga a declaracao e devolve a pessoa as estimativas --
    e o desfazer, para quando alguem digita o numero na linha errada.
    """
    pessoa = db.dicts("SELECT id, full_name FROM members WHERE id = ?", (member_id,))
    if not pessoa:
        raise ValueError(f"ficha {member_id} nao encontrada")
    if valor is not None:
        valor = int(valor)
        if valor < 0:
            raise ValueError("o índice h não pode ser negativo")
        # Nao ha teto real, mas um numero de tres digitos aqui e sempre
        # dedo escorregado -- e um h de 1600 na tela desmoraliza o painel
        # inteiro para quem olha.
        if valor > 300:
            raise ValueError("índice h acima de 300: confira o número digitado")
    db.execute(
        "UPDATE members SET h_index_declarado = ?, h_index_declarado_base = ?,"
        "  h_index_declarado_em = ?, h_index_declarado_por = ? WHERE id = ?",
        (valor, base if valor is not None else None,
         (em or date.today().isoformat()) if valor is not None else None,
         por if valor is not None else None, member_id))
    _aplicar(db, member_id)
    db.conn.commit()
    return {"id": member_id, "quem": pessoa[0]["full_name"], "h_index": valor,
            "base": base, "em": em or date.today().isoformat()}


def _aplicar(db: Database, member_id: int) -> None:
    """Poe a declaracao em `h_index`, que e a coluna que a tela le.

    Sem isto, declarar mudaria uma coluna que ninguem mostra. Quando a
    declaracao e apagada, `h_index` volta a valer o que o calculo do banco
    disser -- e nao fica com o numero declarado orfao.
    """
    linha = db.dicts(
        "SELECT h_index_declarado FROM members WHERE id = ?", (member_id,))
    if not linha:
        return
    declarado = linha[0]["h_index_declarado"]
    if declarado is not None:
        db.execute(
            "UPDATE members SET h_index = ?, h_index_source = 'declarado' WHERE id = ?",
            (declarado, member_id))
        return
    # Apagar a declaracao tem de apagar TAMBEM o numero que ela deixou em
    # `h_index`. Sem isto o valor declarado continuava na tela, agora sem
    # origem e sem data -- passando por estimativa do sistema um numero que
    # ninguem mais assina. E `recalcular_um` nao cobre esse caso: quem nao
    # tem artigo neste banco nao e recalculado, e o resto ficava intacto.
    db.execute(
        "UPDATE members SET h_index = NULL, h_index_source = NULL"
        " WHERE id = ? AND h_index_source = 'declarado'", (member_id,))
    from . import metrics
    metrics.recalcular_um(db, member_id)


def instalar_declarados(db: Database) -> list[dict[str, Any]]:
    """Aplica INDICES_DECLARADOS onde ainda nao ha declaracao.

    So preenche vazio: uma vez que a coordenacao grave o numero pela tela,
    este arquivo nao tem mais nada a dizer sobre aquela pessoa. E se a
    pessoa nao existir no banco, nao faz nada -- nao inventa ficha.
    """
    feitos = []
    fichas = db.dicts("SELECT id, full_name, name_key, h_index_declarado FROM members")
    for nome, valor, base, em in INDICES_DECLARADOS:
        chave = author_key(nome)
        alvo = None
        for ficha in fichas:
            if ficha["name_key"] == chave or author_key(ficha["full_name"]) == chave:
                alvo = ficha
                break
        if alvo is None:
            # casa pelo primeiro nome: "Guilherme" pode estar gravado como
            # "Guilherme Torres" sem que ninguem tenha escrito a variacao
            primeiro = str(nome).strip().split()[0].lower()
            parecidos = [f for f in fichas
                         if str(f["full_name"] or "").strip().lower().split()[:1] == [primeiro]]
            alvo = parecidos[0] if len(parecidos) == 1 else None
        if alvo is None or alvo["h_index_declarado"] is not None:
            continue
        declarar(db, int(alvo["id"]), valor, base=base, por="coordenação", em=em)
        feitos.append({"quem": alvo["full_name"], "h_index": valor, "base": base})
    return feitos


def _meses_desde(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        ano, mes, dia = (int(p) for p in str(iso)[:10].split("-"))
    except (ValueError, TypeError):
        return None
    hoje = date.today()
    return (hoje.year - ano) * 12 + (hoje.month - mes) - (1 if hoje.day < dia else 0)


def situacao(pessoa: dict[str, Any]) -> dict[str, Any]:
    """Como a tela deve apresentar o indice h desta pessoa.

    Devolve o valor, de onde ele vem, ha quanto tempo, e as estimativas
    para comparacao. A divergencia nao e escondida: um declarado de 16 ao
    lado de um OpenAlex de 22 conta ao leitor que o perfil publico esta
    inflado, que e justamente o que nao se via antes.
    """
    declarado = pessoa.get("h_index_declarado")
    meses = _meses_desde(pessoa.get("h_index_declarado_em"))
    estimativas = {
        "banco": pessoa.get("h_index") if pessoa.get("h_index_source") == "banco_lape" else None,
        "scopus": pessoa.get("h_index_scopus"),
        "wos": pessoa.get("h_index_wos"),
    }
    if declarado is None:
        return {"valor": pessoa.get("h_index"), "origem": "estimado",
                "declarado": None, "meses": None, "a_conferir": True,
                "estimativas": estimativas,
                "recado": "Calculado pelo sistema. Ninguém conferiu ainda."}
    velho = meses is not None and meses >= VALIDADE_MESES
    recado = "Conferido em " + str(pessoa.get("h_index_declarado_em") or "")[:10]
    if pessoa.get("h_index_declarado_base"):
        recado += " na " + str(pessoa["h_index_declarado_base"])
    if velho:
        recado += f" — faz {meses} meses, vale reconferir"
    return {"valor": declarado, "origem": "declarado", "declarado": declarado,
            "meses": meses, "a_conferir": velho, "estimativas": estimativas,
            "recado": recado}


def painel(db: Database) -> list[dict[str, Any]]:
    """Uma linha por pesquisador do LAPE, para a tela de conferencia."""
    linhas = db.dicts(
        "SELECT id, full_name, h_index, h_index_source, h_index_scopus, h_index_wos,"
        "       h_index_declarado, h_index_declarado_base, h_index_declarado_em,"
        "       h_index_declarado_por"
        "  FROM members"
        " WHERE COALESCE(is_external, 0) = 0 AND COALESCE(active, 1) = 1"
        " ORDER BY COALESCE(h_index_declarado, h_index, 0) DESC, full_name")
    for linha in linhas:
        linha["situacao"] = situacao(linha)
    return linhas
