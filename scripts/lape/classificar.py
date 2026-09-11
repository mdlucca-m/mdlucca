"""Ligar artigo a linha de pesquisa pelo titulo.

O banco tem 160 artigos e uma parte deles sem linha declarada. Sem linha,
o artigo some de toda leitura que a coordenacao faz por linha: some do
mosaico do painel, do funil, da corrida entre as linhas, e some do
relatorio que o avaliador pede. Ate aqui a unica forma de ligar era abrir
artigo por artigo e escolher no seletor.

O titulo de um artigo cientifico e um resumo escrito por quem conhece o
assunto: "Efeitos do exercicio aerobico na dor e no sono de mulheres com
fibromialgia" nomeia a linha sem deixar duvida. Cada linha declarada ja
carrega as suas palavras-chave (ver `linhas.LINHAS`), e e com elas que a
comparacao e feita.

O QUE ESTE MODULO NAO FAZ, e de proposito:

  - Nao encosta em artigo que ja tem linha. Linha declarada e decisao de
    gente, e palpite de maquina nao sobrescreve decisao de gente. Foi a
    licao do indice h e dos campos apagados.
  - Nao decide no empate. Quando duas linhas empatam, ou quando a
    primeira nao abre vantagem sobre a segunda, o artigo volta como
    "ambiguo" e ninguem o liga a nada. Um palpite errado em silencio e
    pior do que um campo vazio: o campo vazio aparece na aba de
    qualidade, e o palpite errado passa por dado conferido.
  - Nao aplica sozinho. `sugerir` propoe com a evidencia ao lado -- as
    palavras que casaram, e quais --, e `aplicar` so mexe no que a
    coordenacao mandou aplicar.

A comparacao e por palavra inteira e sem acento: "dor" nao pode casar
dentro de "dormir", e "Fibromialgia" tem de casar com "fibromialgia".
Palavra-chave de duas palavras ("dor cronica", "qualidade do ar") casa
como expressao, e vale mais do que uma palavra solta -- quem escreve
"qualidade do ar" no titulo esta falando da linha, e quem escreve "ar"
pode estar falando de qualquer coisa.
"""
from __future__ import annotations

import re
from typing import Any

from .db import Database
from .util import strip_accents

# Vantagem minima da primeira linha sobre a segunda para a sugestao valer.
# Com 1.0 um unico termo a mais ja decide, e um titulo que fala de dor e de
# idoso cairia na primeira que aparecesse; 1.5 exige que a diferenca seja
# de uma expressao, ou de duas palavras soltas.
MARGEM_MINIMA = 1.5
# Abaixo disto nao ha evidencia nenhuma: uma palavra solta num titulo de
# quinze nao liga um artigo a uma linha de pesquisa.
PESO_MINIMO = 2.0
# Expressao vale mais que palavra solta, pela razao do cabecalho. E o
# NOME da linha vale mais do que as palavras-chave dela: "fadiga" e um
# sintoma que varias linhas estudam, mas um titulo que diz "cancer" esta
# falando da linha chamada Cancer. Sem esse degrau, "Exercicio fisico e
# fadiga em sobreviventes de cancer de mama" empatava com a linha de
# exercicio, so porque o titulo tambem diz "exercicio".
PESO_EXPRESSAO = 2.0
PESO_PALAVRA = 1.0
PESO_NOME_EXPRESSAO = 3.0
PESO_NOME_PALAVRA = 2.0

# Palavras que aparecem em quase todo titulo da area e nao distinguem
# linha nenhuma. Deixa-las pontuar faria "efeitos do exercicio" casar com
# todas as linhas ao mesmo tempo.
VAZIAS = frozenset("""
a as o os um uma uns umas de do da dos das em no na nos nas por para com
sem sobre entre e ou que se ao aos à às pelo pela como apos antes durante
efeito efeitos estudo estudos analise avaliacao influencia impacto papel
relacao associacao nivel niveis fatores aspectos revisao sistematica
ensaio clinico randomizado protocolo artigo pesquisa resultados
""".split())


# Boa parte da producao do LAPE e publicada em ingles, e as palavras-chave
# das linhas estao todas em portugues: "Resistance training protocol for
# fibromyalgia" nao casava com uma unica palavra e caia em "sem indicio".
# Nao e traducao automatica nem dicionario geral -- e o vocabulario desta
# area, termo a termo, que e o que aparece em titulo de artigo.
EQUIVALENTES: dict[str, tuple[str, ...]] = {
    "exercicio": ("exercise",),
    "exercicio fisico": ("physical exercise",),
    "atividade fisica": ("physical activity",),
    "treinamento": ("training",),
    "treinamento resistido": ("resistance training", "strength training"),
    "aerobico": ("aerobic",),
    "fibromialgia": ("fibromyalgia",),
    "dor": ("pain",),
    "dor cronica": ("chronic pain",),
    "cronica": ("chronic",),
    "doencas reumaticas": ("rheumatic diseases", "rheumatic disease"),
    "artrite": ("arthritis",),
    "sono": ("sleep",),
    "ansiedade": ("anxiety",),
    "depressao": ("depression",),
    "sintomas depressivos": ("depressive symptoms",),
    "humor": ("mood",),
    "estresse": ("stress",),
    "saude mental": ("mental health",),
    "bem estar": ("well being", "wellbeing"),
    "qualidade de vida": ("quality of life",),
    "idosos": ("older adults", "elderly", "aged"),
    "envelhecimento": ("aging", "ageing"),
    "cognicao": ("cognition", "cognitive"),
    "autonomia funcional": ("functional capacity", "functional autonomy"),
    "cancer": ("cancer",),
    "mama": ("breast",),
    "oncologia": ("oncology",),
    "fadiga": ("fatigue",),
    "poluicao": ("pollution",),
    "qualidade do ar": ("air quality",),
    "material particulado": ("particulate matter",),
    "ozonio": ("ozone",),
    "atletas": ("athletes", "athlete"),
    "esporte": ("sport", "sports"),
    "desempenho": ("performance",),
    "rendimento": ("performance",),
    "competitiva": ("competitive",),
    "coesao de equipe": ("team cohesion",),
    "motivacao": ("motivation",),
    "aderencia": ("adherence",),
    "autoeficacia": ("self efficacy",),
    "escola": ("school",),
    "escolar": ("school",),
    "exergames": ("exergames", "active video games"),
    "reabilitacao": ("rehabilitation",),
    "fisioterapia": ("physiotherapy", "physical therapy"),
    "lesao": ("injury",),
    "prevencao": ("prevention",),
    "criancas": ("children",),
    "adolescentes": ("adolescents",),
    "mulheres": ("women",),
}


def _normalizar(texto: Any) -> str:
    """Minuscula, sem acento, so letras e numeros separados por espaco."""
    limpo = strip_accents(str(texto or "")).lower()
    return " " + re.sub(r"[^a-z0-9]+", " ", limpo).strip() + " "


def _reduzir(texto: Any) -> str:
    """O mesmo texto sem as palavras vazias e sem as de ate duas letras.

    Titulo e palavra-chave PRECISAM passar pelo mesmo filtro. Enquanto so
    a palavra-chave era reduzida, a expressao "qualidade do ar" virava
    "qualidade ar" de um lado e continuava "qualidade do ar" do outro --
    e a linha de Qualidade do ar nao casava com um titulo que a nomeia
    por extenso.
    """
    palavras = [p for p in _normalizar(texto).split() if p not in VAZIAS]
    return " " + " ".join(palavras) + " " if palavras else " "


# As chaves acima estao escritas como se escreve; a comparacao acontece na
# forma reduzida (sem palavras vazias). "qualidade do ar" vira "qualidade
# ar" de um lado e ficava "qualidade do ar" do outro, e a equivalencia
# nunca era encontrada -- a linha de Qualidade do ar continuava sem o
# ingles. Normalizar as chaves uma vez, no carregamento, resolve para
# todas.
_EQUIV: dict[str, tuple[str, ...]] = {}


def _montar_equivalencias() -> None:
    for chave, valores in EQUIVALENTES.items():
        reduzida = _reduzir(chave).strip()
        if reduzida:
            _EQUIV[reduzida] = valores


def _termos_da_linha(linha: dict) -> list[tuple[str, float]]:
    """As expressoes e palavras que caracterizam uma linha, com o peso.

    Vem das palavras-chave declaradas E do proprio nome da linha: uma
    linha chamada "Qualidade do ar" e caracterizada por essa expressao
    mesmo que ninguem a tenha repetido nas palavras-chave.
    """
    termos: dict[str, float] = {}

    def guardar(chave: str, peso: float) -> None:
        if not chave:
            return
        termos[chave] = max(termos.get(chave, 0.0), peso)
        # o mesmo termo em ingles vale o mesmo: o idioma do titulo nao
        # muda o assunto do artigo
        for equivalente in _EQUIV.get(chave, ()):
            reduzido = _reduzir(equivalente).strip()
            if reduzido:
                termos[reduzido] = max(termos.get(reduzido, 0.0), peso)

    # O nome INTEIRO da linha e o sinal mais forte que existe, tenha ele
    # uma palavra ou quatro: um titulo que diz "cancer" esta falando da
    # linha chamada Cancer, e um que diz "qualidade do ar" esta falando da
    # linha Qualidade do ar. Por isso ele entra como termo unico, e nao
    # como a soma das suas palavras.
    guardar(_reduzir(linha.get("name") or "").strip(), PESO_NOME_EXPRESSAO)
    for palavra in _reduzir(linha.get("name") or "").split():
        if len(palavra) > 2:
            guardar(palavra, PESO_NOME_PALAVRA)
    for bruto in re.split(r"[;,/|]", str(linha.get("keywords") or "")):
        palavras = _reduzir(bruto).split()
        if not palavras:
            continue
        if len(palavras) > 1:
            guardar(" ".join(palavras), PESO_EXPRESSAO)
        for palavra in palavras:
            # Palavra de ate duas letras so vale dentro de uma expressao:
            # "ar" sozinho nao caracteriza linha nenhuma, e "qualidade do
            # ar" caracteriza.
            if len(palavra) > 2:
                guardar(palavra, PESO_PALAVRA)
    return sorted(termos.items(), key=lambda par: (-par[1], par[0]))


def _casa(termo: str, titulo: str) -> bool:
    """Palavra inteira, nunca pedaco: "dor" nao casa dentro de "dormir"."""
    return (" " + termo + " ") in titulo


def pontuar(titulo: str, linhas: list[dict]) -> list[dict]:
    """Quanto o titulo puxa para cada linha, e por causa de que palavras."""
    alvo = _reduzir(titulo)
    placar = []
    for linha in linhas:
        peso = 0.0
        provas: list[str] = []
        for termo, valor in _termos_da_linha(linha):
            if not _casa(termo, alvo):
                continue
            # Uma expressao ja contabilizada engole as suas palavras:
            # "dor cronica" nao pode pontuar tres vezes (a expressao,
            # "dor" e "cronica"), senao uma linha com palavras-chave
            # compostas ganharia de todas as outras por construcao. Como
            # os termos vem do maior peso para o menor, a expressao e
            # sempre vista antes das palavras que a compoem.
            if any(" " + termo + " " in " " + prova + " " for prova in provas):
                continue
            peso += valor
            provas.append(termo)
        if peso > 0:
            placar.append({"linha_id": linha["id"], "linha": linha["name"],
                           "peso": round(peso, 2), "termos": provas})
    return sorted(placar, key=lambda x: (-x["peso"], x["linha"]))


def sugerir(db: Database, limite: int = 0) -> dict[str, Any]:
    """Propoe uma linha para cada artigo que esta sem nenhuma.

    Devolve tres listas, e as tres importam: o que da para ligar, o que
    ficou ambiguo (duas linhas disputam) e o que nenhuma palavra alcancou.
    As duas ultimas nao sao falha do metodo -- sao a resposta honesta, e
    dizem onde falta palavra-chave na linha ou onde o titulo e generico.
    """
    linhas = db.dicts(
        "SELECT id, name, keywords FROM research_lines WHERE active = 1 ORDER BY name")
    if not linhas:
        return {"linhas": 0, "sugestoes": [], "ambiguos": [], "sem_indicio": [],
                "total_sem_linha": 0}

    sem_linha = db.dicts(
        "SELECT id, title, internal_code, status, year_published FROM articles"
        " WHERE research_line_id IS NULL ORDER BY COALESCE(year_published, 0) DESC, id")
    sugestoes, ambiguos, sem_indicio = [], [], []
    for artigo in sem_linha:
        placar = pontuar(artigo["title"], linhas)
        topo = placar[0] if placar else None
        segundo = placar[1] if len(placar) > 1 else None
        base = {"artigo_id": artigo["id"], "titulo": artigo["title"],
                "codigo": artigo.get("internal_code"), "status": artigo.get("status"),
                "ano": artigo.get("year_published")}
        if topo is None or topo["peso"] < PESO_MINIMO:
            sem_indicio.append({**base, "melhor": topo["linha"] if topo else None,
                                "peso": topo["peso"] if topo else 0})
            continue
        margem = topo["peso"] - (segundo["peso"] if segundo else 0.0)
        if segundo is not None and margem < MARGEM_MINIMA:
            ambiguos.append({**base, "disputam": [topo["linha"], segundo["linha"]],
                             "pesos": [topo["peso"], segundo["peso"]],
                             "termos": topo["termos"] + segundo["termos"]})
            continue
        sugestoes.append({**base, "linha_id": topo["linha_id"], "linha": topo["linha"],
                          "peso": topo["peso"], "margem": round(margem, 2),
                          "termos": topo["termos"],
                          "segundo": segundo["linha"] if segundo else None})
    if limite:
        sugestoes = sugestoes[:limite]
    return {"linhas": len(linhas), "sugestoes": sugestoes, "ambiguos": ambiguos,
            "sem_indicio": sem_indicio, "total_sem_linha": len(sem_linha)}


def aplicar(db: Database, pares: list[dict], actor: str | None = None) -> dict[str, Any]:
    """Grava as ligacoes que a coordenacao aprovou.

    `pares` e uma lista de {artigo_id, linha_id}. Artigo que ja ganhou
    linha nesse meio-tempo e pulado, e nao sobrescrito: entre o momento da
    sugestao e o do clique, alguem pode ter cadastrado a linha na mao, e
    essa mao vale mais do que esta conta.
    """
    ligados, pulados = 0, []
    for par in pares or []:
        artigo_id = int(par.get("artigo_id") or par.get("id") or 0)
        linha_id = int(par.get("linha_id") or 0)
        if not artigo_id or not linha_id:
            continue
        atual = db.dicts("SELECT research_line_id, title FROM articles WHERE id = ?",
                         (artigo_id,))
        if not atual:
            pulados.append({"artigo_id": artigo_id, "motivo": "artigo não existe mais"})
            continue
        if atual[0]["research_line_id"] is not None:
            pulados.append({"artigo_id": artigo_id,
                            "motivo": "já ganhou linha desde a sugestão"})
            continue
        if not db.dicts("SELECT id FROM research_lines WHERE id = ?", (linha_id,)):
            pulados.append({"artigo_id": artigo_id, "motivo": "linha não existe"})
            continue
        db.execute(
            "UPDATE articles SET research_line_id = ?,"
            "       updated_at = datetime('now') WHERE id = ?",
            (linha_id, artigo_id))
        ligados += 1
    if ligados:
        db.conn.commit()
    return {"ligados": ligados, "pulados": pulados, "por": actor}


_montar_equivalencias()
