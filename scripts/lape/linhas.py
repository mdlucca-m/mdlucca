"""As linhas de pesquisa do LAPE, como o laboratorio as declarou.

Ficam escritas aqui pelo mesmo motivo do vocabulario de variaveis: sao a
espinha do laboratorio, mudam de ano em ano e nao de dia em dia, e ter de
redigita-las a cada instalacao e um convite a divergencia -- uma maquina
com "Psicologia do Esporte", outra com "Psicologia do esporte", e o painel
contando duas linhas onde ha uma.

A lista e fechada: o formulario de artigo oferece estas oito e mais
nenhuma. Uma linha que sai da lista nao e apagada -- e desativada, e sai
das opcoes continuando a existir para os artigos que ja apontavam para
ela. Apagar tiraria do ar a historia de quem publicou naquilo.

Instalar de novo nao apaga o que foi mexido: o `code` e a chave, e uma
linha ja existente so tem preenchido o que estiver em branco. O nome e a
excecao, e so quando a linha ainda tem um nome que este arquivo mesmo
escreveu em alguma versao anterior -- ai e uma correcao de nomenclatura,
nao um atropelo. Quem renomeou a mao para algo que nunca esteve aqui
continua com o que escreveu.
"""
from __future__ import annotations

from typing import Any

from .db import Database

# (codigo, nome, descricao, palavras-chave, icone)
# As palavras-chave nao sao enfeite: e por elas que a busca da tela
# encontra a linha, e sao a ponte com o vocabulario de variaveis.
LINHAS: tuple[tuple[str, str, str, str, str], ...] = (
    ("psicologia_do_esporte", "Psicologia do esporte",
     "Estuda a mente sob competição. Ansiedade pré-competitiva, foco, coesão de "
     "equipe e regulação emocional respondem por parte do desempenho que o "
     "treinamento físico, sozinho, não explica.",
     "esporte; atletas; ansiedade competitiva; desempenho; coesão de equipe",
     "trofeu"),
    ("psicologia_exercicio", "Psicologia do exercício",
     "Examina os processos psicológicos que sustentam a prática regular de "
     "exercício. A pergunta central não é o que o corpo faz, e sim o que leva "
     "alguém a começar, a permanecer e a voltar depois da interrupção.",
     "exercício; motivação; aderência; humor; bem-estar; autoeficácia",
     "halteres"),
    ("exercicio_fibromialgia", "Fibromialgia e doenças reumáticas",
     "Trata o exercício como intervenção clínica na fibromialgia e nas demais "
     "doenças reumáticas. Dor difusa, sono fragmentado, fadiga e sintomas "
     "depressivos respondem à carga, à intensidade e à progressão, e é essa dose "
     "que a linha procura estabelecer.",
     "fibromialgia; doenças reumáticas; artrite; dor crônica; treinamento resistido; "
     "impacto da doença; sono",
     "dor"),
    ("qualidade_do_ar", "Qualidade do ar",
     "Mede o custo de treinar no ar que há. O exercício multiplica o volume "
     "respirado, e com ele a dose de material particulado que alcança o pulmão "
     "de quem corre, pedala ou compete a céu aberto.",
     "poluição; qualidade do ar; material particulado; exercício ao ar livre; ozônio",
     "pulmao"),
    ("exercicio_cancer", "Câncer",
     "Acompanha o exercício ao longo do tratamento oncológico e depois dele. "
     "Fadiga, ansiedade, sintomas depressivos e qualidade de vida constituem os "
     "desfechos, em pacientes cuja tolerância ao esforço muda de semana para semana.",
     "câncer; oncologia; fadiga; depressão; ansiedade; qualidade de vida",
     "fita"),
    ("exercicio_envelhecimento", "Envelhecimento",
     "Observa o que o exercício preserva quando os anos avançam. Cognição, humor, "
     "autonomia funcional e vínculo social envelhecem em ritmos distintos, e a "
     "prática regular altera esse ritmo.",
     "envelhecimento; idosos; cognição; depressão; autonomia funcional",
     "envelhecimento"),
    ("fisioterapia", "Fisioterapia",
     "Avalia a reabilitação como tratamento: o que a conduta fisioterapêutica "
     "devolve em função, dor e independência, e em quanto tempo. Inclui o que a "
     "pessoa sente sobre o próprio corpo durante a recuperação, e não apenas o "
     "que a medida objetiva registra.",
     "fisioterapia; reabilitação; funcionalidade; lesão; dor; amplitude de movimento",
     "dor"),
    ("exergames_escolas", "Exergames e escolas",
     "Leva o jogo com movimento para dentro da escola e mede o que ele produz. "
     "Aptidão, atenção, humor e engajamento de crianças e adolescentes constituem "
     "os desfechos, num contexto em que a adesão importa tanto quanto a dose.",
     "exergames; jogos ativos; escola; crianças; adolescentes; educação física; "
     "engajamento",
     "corrida"),
)

# Nomes que ESTE arquivo ja escreveu em versoes anteriores. Servem para
# distinguir a linha que o sistema instalou -- e que pode ser renomeada
# quando a coordenacao redeclara a nomenclatura -- da linha que alguem
# renomeou a mao na tela, que nao se toca.
NOMES_ANTERIORES: dict[str, tuple[str, ...]] = {
    "psicologia_do_esporte": ("Psicologia do Esporte",),
    "psicologia_exercicio": ("Psicologia do Exercício",),
    "exercicio_fibromialgia": ("Exercício na saúde física e mental na Fibromialgia",),
    "qualidade_do_ar": ("Qualidade do ar e poluição no exercício e no esporte",),
    "exercicio_cancer": ("Exercício na saúde mental no tratamento do câncer",),
    "exercicio_envelhecimento": ("Exercício na saúde mental no envelhecimento",),
}

# O que aponta para uma linha. Desativar nao apaga nada, mas a coordenacao
# precisa saber quanta coisa ficou pendurada numa opcao que saiu da lista,
# senao a linha some da tela levando junto a contagem de quem publicou ali.
APONTAM_PARA_LINHA: tuple[tuple[str, str], ...] = (
    ("articles", "Artigos"),
    ("members", "Pessoas"),
    ("projects", "Projetos"),
    ("events", "Atividades"),
)


def _achar(db: Database, codigo: str, nome: str):
    """A linha que ja existe, se existir -- por codigo, nome novo ou nome antigo.

    So por codigo, uma linha antiga que por acaso ocupasse o mesmo codigo
    engoliria a nova em silencio: foi o que aconteceu com "Psicologia do
    Esporte", que ficou de fora porque o banco ja tinha "Psicologia do
    Esporte e do Exercicio" no codigo `psicologia_esporte`. So por nome,
    uma linha renomeada a mao viraria duas -- e, depois desta redeclaracao
    de nomenclatura, tambem viraria duas a linha que ainda esta gravada
    com o nome antigo. As tres perguntas cobrem os tres casos, e a
    comparacao de nome ignora caixa e acento.
    """
    from .util import norm_key

    achado = db.dicts(
        "SELECT id, name, code FROM research_lines WHERE code = ? OR name = ?",
        (codigo, nome))
    if achado:
        return achado[0]
    alvos = {norm_key(nome)}
    alvos.update(norm_key(antigo) for antigo in NOMES_ANTERIORES.get(codigo, ()))
    for linha in db.dicts("SELECT id, name, code FROM research_lines"):
        if norm_key(linha["name"]) in alvos:
            return linha
    return None


def _pode_renomear(codigo: str, atual: str, novo: str) -> bool:
    """Se o nome gravado e um que este arquivo mesmo escreveu.

    Renomear "Exercício na saúde física e mental na Fibromialgia" para
    "Fibromialgia e doenças reumáticas" e corrigir a nomenclatura que o
    proprio sistema instalou. Renomear o que a coordenacao digitou na tela
    seria outra coisa: apagar a decisao dela e ainda dizer "linha
    atualizada". Na duvida, nao mexe -- e reporta.
    """
    from .util import norm_key

    se_iguala = {norm_key(novo)}
    se_iguala.update(norm_key(antigo) for antigo in NOMES_ANTERIORES.get(codigo, ()))
    return norm_key(atual) in se_iguala


def _quanto_aponta(db: Database, linha_id: int) -> dict[str, int]:
    """Quantos registros de cada tipo ainda apontam para a linha."""
    quanto = {}
    for tabela, rotulo in APONTAM_PARA_LINHA:
        n = db.scalar(
            f"SELECT COUNT(*) FROM {tabela} WHERE research_line_id = ?", (linha_id,))
        if n:
            quanto[rotulo] = int(n)
    return quanto


def instalar(db: Database, encerrar_as_que_sairam: bool = False) -> dict[str, Any]:
    """Poe as oito linhas no banco.

    `encerrar_as_que_sairam` tira das opcoes toda linha que nao esta na
    lista declarada. Vem desligado de proposito: `instalar` roda a cada
    subida do servidor, e uma linha que o laboratorio criou a mao na tela
    nao pode sumir do seletor porque a maquina reiniciou. Encerrar e
    decisao da coordenacao, tomada no botao -- e o botao mostra na hora o
    que saiu e quantos registros ficaram pendurados.
    """
    from .util import norm_key

    novas, ja_havia, renomeadas, nome_proprio = [], [], [], []
    canonicas: set[int] = set()
    for codigo, nome, descricao, palavras, _icone in LINHAS:
        achado = _achar(db, codigo, nome)
        if achado:
            canonicas.add(int(achado["id"]))
            # Preenche buraco pelo ID -- nao pelo codigo. Gravar por codigo
            # criaria uma segunda linha quando a existente foi encontrada
            # pelo nome e tem outro codigo.
            db.execute(
                "UPDATE research_lines"
                "   SET description = COALESCE(NULLIF(TRIM(description), ''), ?),"
                "       keywords    = COALESCE(NULLIF(TRIM(keywords), ''), ?),"
                "       active      = 1"
                " WHERE id = ?",
                (descricao, palavras, achado["id"]))
            atual = achado["name"] or ""
            if norm_key(atual) == norm_key(nome) and atual != nome:
                # so a caixa difere: alinha sem alarde
                db.execute("UPDATE research_lines SET name = ? WHERE id = ?",
                           (nome, achado["id"]))
                ja_havia.append(nome)
            elif atual != nome and _pode_renomear(codigo, atual, nome):
                db.execute("UPDATE research_lines SET name = ? WHERE id = ?",
                           (nome, achado["id"]))
                renomeadas.append({"de": atual, "para": nome})
            elif atual != nome:
                nome_proprio.append({"gravado": atual, "declarado": nome})
                ja_havia.append(atual)
            else:
                ja_havia.append(nome)
            continue
        criada = db.upsert("research_lines", {
            "code": codigo, "name": nome, "description": descricao,
            "keywords": palavras, "active": 1,
        }, conflict=("code",))
        canonicas.add(int(criada))
        novas.append(nome)

    # O que sobrou sai das opcoes sem ser apagado. Uma linha antiga com
    # trinta artigos pendurados continua existindo e continua contando --
    # so deixa de aparecer na lista de quem cadastra artigo novo.
    desativadas = []
    if encerrar_as_que_sairam:
        for linha in db.dicts(
                "SELECT id, name FROM research_lines WHERE COALESCE(active, 1) = 1"):
            if int(linha["id"]) in canonicas:
                continue
            db.execute("UPDATE research_lines SET active = 0 WHERE id = ?", (linha["id"],))
            desativadas.append({"nome": linha["name"], "id": int(linha["id"]),
                                "aponta": _quanto_aponta(db, int(linha["id"]))})
    db.conn.commit()
    return {"novas": novas, "ja_havia": ja_havia, "renomeadas": renomeadas,
            "nome_proprio": nome_proprio, "desativadas": desativadas,
            "total": len(LINHAS)}


def icone_de(codigo: str | None, nome: str | None) -> str:
    """O icone da linha, pelo codigo ou pelo nome -- "linha" quando nao ha.

    Precisa das duas perguntas pelo mesmo motivo de `_achar`: uma linha
    instalada aqui pode ter sido encontrada pelo nome e guardada com outro
    codigo, e ai a busca so por codigo devolveria o icone generico para uma
    linha que tem o seu. O nome antigo tambem responde, para a linha que
    ficou com o nome de antes nao perder o icone. Uma linha que o
    laboratorio criou a mao continua com o icone neutro, e isso e o certo:
    inventar "corrida" para uma linha que ninguem descreveu seria a tela
    afirmando o que nao sabe.
    """
    from .util import norm_key

    if codigo:
        for c, _n, _d, _p, icone in LINHAS:
            if c == codigo:
                return icone
    if nome:
        alvo = norm_key(nome)
        for c, n, _d, _p, icone in LINHAS:
            if norm_key(n) == alvo:
                return icone
            if any(norm_key(a) == alvo for a in NOMES_ANTERIORES.get(c, ())):
                return icone
    return "linha"
