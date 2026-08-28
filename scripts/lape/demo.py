"""Massa de teste do LAPE — dados fictícios com a forma dos dados reais.

Para que serve
  Ver o sistema inteiro funcionando antes de a planilha do laboratório estar
  completa: todos os gráficos plotados, o lakehouse com histórico, a rede de
  colaboração povoada, o calendário cheio e o ciclo editorial com tempos.

O que ela NÃO é
  Não é dado do LAPE. Os nomes de pessoas, títulos, DOIs e números são
  inventados. Por isso a massa nasce num banco separado (`data/demo.sqlite`)
  e num painel separado (`docs/demo.html`): rodar isto nunca toca no banco de
  produção, e o painel gerado diz em toda página que é simulação.

Como ela é construída
  As linhas saem daqui com os **mesmos nomes de coluna das planilhas** e
  entram pelos mesmos `ingest_*` que leem os arquivos reais. Ou seja: a massa
  também testa o mapeamento de colunas, a fusão de nomes de autor, a derivação
  de status e o cálculo de datas — não só o desenho dos gráficos.

Determinismo
  Mesma semente, mesma massa. As datas são ancoradas em `hoje`, para que o
  calendário sempre tenha atividades passadas e futuras.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------
# Vocabulários. Nomes de pessoas são fictícios de propósito.
# ----------------------------------------------------------------------
LINHAS = [
    ("Psicologia do exercício e saúde mental", "PEX",
     "Efeitos do exercício sobre ansiedade, depressão e qualidade de vida.",
     "exercício; saúde mental; ansiedade; depressão; qualidade de vida"),
    ("Treinamento psicológico no esporte de rendimento", "TPR",
     "Habilidades psicológicas, rotinas pré-competitivas e desempenho.",
     "treinamento mental; imagética; rotina pré-competitiva; rendimento"),
    ("Dor crônica, fibromialgia e movimento", "DOR",
     "Intervenções com exercício em condições de dor persistente.",
     "fibromialgia; dor crônica; exercício; catastrofização"),
    ("Comportamento sedentário e aderência", "CSA",
     "Determinantes da adesão à prática e do tempo sentado.",
     "aderência; comportamento sedentário; motivação; autodeterminação"),
    ("Neurociência do exercício e cognição", "NEC",
     "Função executiva, humor e marcadores neurofisiológicos.",
     "função executiva; cognição; EEG; humor"),
]

PESSOAS = [
    # (nome, curto, vínculo, titulação, linha, externo, índice do orientador)
    # O vínculo usa o vocabulário de mapping.VINCULOS, e o orientador é o que
    # monta o organograma -- sem ele, todo mundo viraria raiz da árvore.
    ("Marina Rossetto Cardoso", "Cardoso MR", "coordenacao", "Doutorado", 0, False, None),
    ("Otávio Bernardes Lemos", "Lemos OB", "professor", "Doutorado", 1, False, None),
    ("Helena Krieger Sampaio", "Sampaio HK", "professor", "Doutorado", 2, False, None),
    ("Rafael Nogueira Bittencourt", "Bittencourt RN", "professor", "Doutorado", 4, False, None),
    ("Camila Deodoro Vasques", "Vasques CD", "pos_doutorado", "Doutorado", 0, False, 0),
    ("Tiago Meireles Farias", "Farias TM", "doutorando", "Mestrado", 1, False, 1),
    ("Larissa Pilger Antunes", "Antunes LP", "doutorando", "Mestrado", 2, False, 2),
    ("Bruno Sartori Cavalheiro", "Cavalheiro BS", "doutorando", "Mestrado", 3, False, 0),
    ("Júlia Kunzler Amaral", "Amaral JK", "doutorando", "Mestrado", 4, False, 3),
    ("Eduardo Rampinelli Souza", "Souza ER", "mestrando", "Graduação", 0, False, 0),
    ("Nathália Bregantin Costa", "Costa NB", "mestrando", "Graduação", 1, False, 1),
    ("Vinícius Haeser Portela", "Portela VH", "mestrando", "Graduação", 2, False, 2),
    ("Isabela Marchi Fontanella", "Fontanella IM", "mestrando", "Graduação", 3, False, 0),
    ("Gustavo Zilli Trevisan", "Trevisan GZ", "mestrando", "Graduação", 4, False, 3),
    ("Ana Clara Bonfim Ribas", "Ribas ACB", "bolsista_ic", "Graduação", 0, False, 0),
    ("Pedro Lauth Meurer", "Meurer PL", "bolsista_ic", "Graduação", 1, False, 1),
    ("Manuela Sperb Coelho", "Coelho MS", "bolsista_extensao", "Graduação", 2, False, 2),
    ("Lucas Werneck Prazeres", "Prazeres LW", "voluntario", "Graduação", 3, False, 0),
    ("Rodrigo Alencastro Vieira", "Vieira RA", "graduando", "Graduação", 4, False, 3),
    ("Beatriz Nunes Delgado", "Delgado BN", "tecnico", "Especialização", 4, False, None),
    ("Ricardo Salvatierra Pinto", "Pinto RS", "colaborador", "Doutorado", 1, True, None),
    ("Sofia Marques Rebelo", "Rebelo SM", "colaborador", "Doutorado", 0, True, None),
    ("Andreu Ferrer Solans", "Ferrer Solans A", "colaborador", "Doutorado", 4, True, None),
    ("Patricia Oakley Hall", "Hall PO", "colaborador", "Doutorado", 2, True, None),
]

# Trabalho de formação por vínculo: (tipo, meses até a conclusão prevista).
# Extensão e voluntariado não têm trabalho de conclusão -- e o organograma
# tem de aguentar a lacuna sem inventar prazo para quem não tem.
FORMACAO = {
    "doutorando": ("tese", (14, 34)),
    "mestrando": ("dissertacao", (6, 20)),
    "bolsista_ic": ("relatorio", (5, 11)),
    "graduando": ("tcc", (4, 12)),
    "pos_doutorado": ("projeto", (8, 22)),
}
BOLSAS = {
    "doutorando": ("CAPES — Demanda Social", (12, 30)),
    "mestrando": ("CNPq — Mestrado", (6, 18)),
    "bolsista_ic": ("PIBIC/CNPq", (4, 10)),
    "bolsista_extensao": ("PROBOLSA/UDESC", (4, 10)),
    "pos_doutorado": ("FAPESC — Pós-doutorado", (6, 16)),
}
MODALIDADES = [
    "handebol", "ginástica rítmica", "futebol", "natação", "atletismo",
    "musculação", "corrida de rua", "voleibol", "ciclismo", "judô",
]
SITUACOES_DA_TESE = [("em_andamento", 3.0), ("coleta", 1.6), ("analise", 1.2),
                     ("qualificacao", 0.9), ("defesa_marcada", 0.4)]

INSTITUICOES = [
    ("Universidade do Estado de Santa Catarina", "UDESC", "Florianópolis", "SC", "Brasil", -27.5949, -48.5482),
    ("Universidade Federal de Santa Catarina", "UFSC", "Florianópolis", "SC", "Brasil", -27.6006, -48.5194),
    ("Universidade Federal do Rio Grande do Sul", "UFRGS", "Porto Alegre", "RS", "Brasil", -30.0346, -51.2177),
    ("Universidade de São Paulo", "USP", "São Paulo", "SP", "Brasil", -23.5505, -46.6333),
    ("Universidade Estadual de Campinas", "Unicamp", "Campinas", "SP", "Brasil", -22.9056, -47.0608),
    ("Universidade Federal de Minas Gerais", "UFMG", "Belo Horizonte", "MG", "Brasil", -19.9167, -43.9345),
    ("Universidade Federal do Paraná", "UFPR", "Curitiba", "PR", "Brasil", -25.4284, -49.2733),
    ("Universidade de Lisboa", "ULisboa", "Lisboa", None, "Portugal", 38.7223, -9.1393),
    ("Universitat de Barcelona", "UB", "Barcelona", None, "Espanha", 41.3874, 2.1686),
    ("University of Birmingham", "UoB", "Birmingham", None, "Reino Unido", 52.4508, -1.9305),
]

# (periódico, ISSN, Qualis, fator de impacto, aceita com que facilidade 0-1)
REVISTAS = [
    ("Psychology of Sport and Exercise", "1469-0292", "A1", 3.4, 0.30),
    ("Journal of Sports Sciences", "0264-0414", "A1", 3.9, 0.28),
    ("Frontiers in Psychology", "1664-1078", "A2", 3.2, 0.62),
    ("International Journal of Sport Psychology", "0047-0767", "A4", 1.1, 0.55),
    ("Revista Brasileira de Medicina do Esporte", "1517-8692", "B1", 0.6, 0.72),
    ("Motriz: Revista de Educação Física", "1980-6574", "A4", 0.9, 0.68),
    ("Journal of Psychosomatic Research", "0022-3999", "A1", 3.5, 0.26),
    ("Pain Medicine", "1526-2375", "A1", 2.9, 0.24),
    ("BMC Public Health", "1471-2458", "A2", 4.5, 0.48),
    ("Scandinavian Journal of Medicine & Science in Sports", "0905-7188", "A1", 4.2, 0.22),
    ("Revista Brasileira de Ciências do Esporte", "0101-3289", "B2", 0.4, 0.75),
    ("Perceptual and Motor Skills", "0031-5125", "B1", 1.3, 0.58),
]

MOTIVOS = [
    ("Fora do escopo da revista", "escopo"),
    ("Amostra insuficiente", "metodo"),
    ("Delineamento com limitações", "metodo"),
    ("Análise estatística inadequada", "analise"),
    ("Redação e clareza do texto", "redacao"),
    ("Contribuição original insuficiente", "originalidade"),
    ("Revisão de literatura desatualizada", "referencial"),
    ("Aspectos éticos não detalhados", "etica"),
    ("Excesso de autocitação", "referencial"),
    ("Formatação fora das normas", "formatacao"),
]

TIPOS_ESTUDO = [
    ("Ensaio clínico randomizado", 0.16), ("Estudo transversal", 0.26),
    ("Coorte prospectiva", 0.12), ("Revisão sistemática", 0.14),
    ("Metanálise", 0.07), ("Estudo qualitativo", 0.11),
    ("Estudo de caso", 0.06), ("Protocolo de estudo", 0.08),
]

TEMAS = {
    0: ["ansiedade competitiva", "sintomas depressivos", "qualidade de vida",
        "bem-estar psicológico", "estresse percebido", "autoestima corporal"],
    1: ["rotina pré-competitiva", "imagética motora", "autofala instrucional",
        "coesão de equipe", "resiliência esportiva", "atenção plena no treino"],
    2: ["fibromialgia", "dor lombar crônica", "catastrofização da dor",
        "cinesiofobia", "limiar de dor por pressão", "fadiga persistente"],
    3: ["comportamento sedentário", "aderência ao exercício", "motivação autônoma",
        "tempo sentado no trabalho", "barreiras para a prática", "autoeficácia"],
    4: ["função executiva", "memória de trabalho", "atividade cortical",
        "variabilidade da frequência cardíaca", "humor pós-exercício", "tempo de reação"],
}
POPULACOES = [
    "atletas de handebol", "nadadores master", "mulheres com fibromialgia",
    "adolescentes escolares", "idosos comunitários", "corredores amadores",
    "jogadores de futebol de base", "servidores públicos", "estudantes universitários",
    "pacientes em reabilitação cardíaca", "praticantes de musculação",
    "atletas paralímpicos", "ginastas em formação", "professores da rede pública",
]
DESENHOS = [
    "um ensaio randomizado de 12 semanas", "um estudo transversal",
    "uma coorte de dois anos", "uma revisão sistemática com metanálise",
    "um estudo qualitativo com grupos focais", "um protocolo de intervenção",
    "um estudo observacional multicêntrico", "uma análise de mediação",
]
IDIOMAS = [("Português", 0.42), ("Inglês", 0.53), ("Espanhol", 0.05)]

EVENTOS = [
    ("reuniao", "Reunião semanal do LAPE", "Sala 204 — Bloco A", 0.42),
    ("coleta", "Coleta de dados", "Laboratório de esforço", 0.16),
    ("seminario", "Seminário de leitura crítica", "Sala 204 — Bloco A", 0.12),
    ("defesa", "Defesa de dissertação", "Auditório do CEFID", 0.06),
    ("qualificacao", "Qualificação de doutorado", "Sala de reuniões da pós", 0.05),
    ("congresso", "Congresso científico", None, 0.08),
    ("curso", "Curso de análise de dados", "Laboratório de informática", 0.05),
    ("extensao", "Ação de extensão na comunidade", "Centro comunitário", 0.04),
    ("visita_tecnica", "Visita técnica", None, 0.02),
]

# Tempo maximo que um manuscrito passa com o periodico antes de a geracao
# considerar que a historia terminou (em recusa). Em dias.
ESPERA_MAXIMA = 540

PROJETOS = [
    ("Exercício e saúde mental em adultos jovens: ensaio multicêntrico", "PEX-001",
     "CNPq", "Universal 2022", 0, "pesquisa", 318000, -3, None),
    ("Treinamento psicológico em atletas de base: efeitos sobre o rendimento", "TPR-002",
     "FAPESC", "Chamada 12/2023", 1, "pesquisa", 145000, -2, None),
    ("Movimento e dor persistente: protocolo aquático para fibromialgia", "DOR-003",
     "CAPES", "PROAP", 2, "pesquisa", 92000, -4, -1),
    ("Menos tempo sentado: intervenção no ambiente de trabalho", "CSA-004",
     "UDESC", "PIBIC", 3, "extensao", 24000, -1, None),
    ("Exercício e função executiva no envelhecimento", "NEC-005",
     "CNPq", "Produtividade em Pesquisa", 4, "pesquisa", 210000, -5, -2),
    ("Rede colaborativa de psicologia do esporte Brasil–Ibéria", "COL-006",
     "CAPES", "PrInt", 1, "cooperacao", 480000, -2, None),
    ("Observatório da produção científica do laboratório", "OBS-007",
     None, None, 0, "institucional", None, -1, None),
]


def _pick(rng: random.Random, pairs: list[tuple[Any, float]]) -> Any:
    """Sorteio com peso, sem depender de random.choices para ser reproduzível."""
    total = sum(w for _, w in pairs)
    mark = rng.random() * total
    running = 0.0
    for value, weight in pairs:
        running += weight
        if mark <= running:
            return value
    return pairs[-1][0]


def _iso(day: date) -> str:
    return day.isoformat()


def _titulo(rng: random.Random, linha: int) -> str:
    tema = rng.choice(TEMAS[linha])
    pop = rng.choice(POPULACOES)
    forma = rng.random()
    if forma < 0.34:
        return f"Efeitos do exercício sobre {tema} em {pop}: {rng.choice(DESENHOS)}"
    if forma < 0.58:
        return f"{tema.capitalize()} em {pop}: associações com a prática regular"
    if forma < 0.78:
        return f"Intervenção psicológica e {tema} em {pop}"
    return f"{tema.capitalize()} e desempenho em {pop}: {rng.choice(DESENHOS)}"


def build(seed: int = 20260826, n_artigos: int = 160,
          hoje: date | None = None) -> dict[str, list[dict]]:
    """Monta a massa como linhas de planilha, em português, prontas para ingestão."""
    rng = random.Random(seed)
    hoje = hoje or date.today()
    ano_atual = hoje.year

    linhas = [{"Linha de pesquisa": nome, "Código": cod, "Descrição": desc,
               "Palavras-chave": kw, "Coordenação": PESSOAS[0][0],
               "Início": _iso(date(ano_atual - 8, 3, 1)), "Ativa": "Sim"}
              for nome, cod, desc, kw in LINHAS]

    instituicoes = [{"Instituição": nome, "Sigla": sigla, "Cidade": cidade, "Estado": uf,
                     "País": pais, "Latitude": lat, "Longitude": lon}
                    for nome, sigla, cidade, uf, pais, lat, lon in INSTITUICOES]

    motivos = [{"Motivo": rotulo, "Categoria": categoria, "Código": f"M{i + 1:02d}"}
               for i, (rotulo, categoria) in enumerate(MOTIVOS)]

    integrantes = []
    for i, (nome, curto, funcao, titulacao, linha, externo, orientador) in enumerate(PESSOAS):
        entrada = date(ano_atual - rng.randint(1, 8), rng.randint(1, 12), rng.randint(1, 28))
        pessoa = {
            "Nome": nome, "Nome curto": curto, "Função": funcao, "Titulação": titulacao,
            "Linha de pesquisa": LINHAS[linha][0],
            "Instituição": INSTITUICOES[0][0] if not externo
                           else INSTITUICOES[rng.randint(1, len(INSTITUICOES) - 1)][0],
            "E-mail": None if externo else
                      curto.split()[0].lower().replace("ú", "u") + f"{i}@exemplo.udesc.br",
            "ORCID": f"0000-000{rng.randint(1, 3)}-{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}",
            "Lattes": str(rng.randint(10 ** 15, 10 ** 16 - 1)),
            "Entrada": _iso(entrada), "Externo": "Sim" if externo else "Não", "Ativo": "Sim",
        }
        if orientador is not None:
            pessoa["Orientador"] = PESSOAS[orientador][0]
            # coorientação existe, mas é minoria: uma em cada três, e nunca
            # apontando para o próprio orientador
            outros = [p[0] for j, p in enumerate(PESSOAS)
                      if p[2] in ("professor", "coordenacao", "pos_doutorado")
                      and j != orientador and j != i]
            if outros and rng.random() < 0.34:
                pessoa["Coorientador"] = rng.choice(outros)
        if funcao in FORMACAO:
            tipo, (menos, mais) = FORMACAO[funcao]
            prazo = hoje + timedelta(days=rng.randint(menos * 30, mais * 30))
            pessoa["Tipo de trabalho"] = tipo
            pessoa["Título da tese"] = _titulo(rng, linha)
            pessoa["Situação da tese"] = _pick(rng, SITUACOES_DA_TESE)
            pessoa["Prazo para conclusão"] = _iso(prazo)
        if funcao in BOLSAS:
            agencia, (menos, mais) = BOLSAS[funcao]
            pessoa["Bolsa"] = agencia
            pessoa["Fim da bolsa"] = _iso(
                hoje + timedelta(days=rng.randint(menos * 30, mais * 30)))
        if not externo:
            pessoa["Temas"] = "; ".join(rng.sample(MODALIDADES, rng.randint(1, 3)))
        integrantes.append(pessoa)

    projetos, projeto_membros = [], []
    for nome, cod, financiadora, edital, linha, tipo, valor, ini, fim in PROJETOS:
        inicio = date(ano_atual + ini, rng.randint(1, 12), 1)
        termino = date(ano_atual + fim, rng.randint(1, 12), 28) if fim is not None else None
        equipe = [PESSOAS[0][0]] + [p[0] for p in PESSOAS[1:]
                                    if p[4] == linha and rng.random() < 0.62][:6]
        projetos.append({
            "Projeto": nome, "Código": cod, "Financiadora": financiadora,
            "Número do processo": edital, "Linha de pesquisa": LINHAS[linha][0],
            "Tipo": tipo, "Valor": valor, "Início": _iso(inicio),
            "Término": _iso(termino) if termino else None,
            "Situação": "concluido" if termino and termino < hoje else "em_andamento",
            "Equipe": "; ".join(equipe),
        })
        for pos, quem in enumerate(equipe):
            projeto_membros.append({
                "Projeto": nome, "Integrante": quem,
                "Papel": "coordenacao" if pos == 0 else
                         ("pesquisador" if pos < 3 else "bolsista"),
                "Entrada": _iso(inicio),
            })

    artigos, submissoes, citacoes = [], [], []
    titulos_usados: set[str] = set()
    for n in range(n_artigos):
        linha = _pick(rng, [(i, w) for i, w in enumerate([1.35, 1.15, 1.0, 0.8, 0.9])])
        # o título é a chave do artigo no banco: repetir viraria um registro só
        # anos recentes concentram mais produção — o laboratório cresceu
        idade_anos = _pick(rng, [(0, 1.5), (1, 1.9), (2, 1.7), (3, 1.4),
                                 (4, 1.1), (5, 0.8), (6, 0.5), (7, 0.3)])
        inicio = hoje - timedelta(days=idade_anos * 365 + rng.randint(0, 360))
        titulo = _titulo(rng, linha)
        tentativas_titulo = 0
        while titulo in titulos_usados and tentativas_titulo < 30:
            titulo = _titulo(rng, linha)
            tentativas_titulo += 1
        if titulo in titulos_usados:
            titulo = f"{titulo} (parte {n})"
        titulos_usados.add(titulo)
        equipe_linha = [p for p in PESSOAS if p[4] == linha]
        outros = [p for p in PESSOAS if p[4] != linha and not p[5]]
        autores = rng.sample(equipe_linha, min(len(equipe_linha), rng.randint(2, 4)))
        if rng.random() < 0.45 and outros:
            autores.append(rng.choice(outros))
        if rng.random() < 0.72:                       # a coordenação assina a maioria
            autores.append(PESSOAS[0])
        vistos, unicos = set(), []
        for pessoa in autores:
            if pessoa[0] not in vistos:
                vistos.add(pessoa[0])
                unicos.append(pessoa)
        # ordem de autoria como num laboratório: quem escreveu vem primeiro,
        # os demais no meio, a coordenação por último
        PESO = {"doutorando": 0, "mestrando": 1, "pos_doutorado": 2, "graduando": 3,
                "bolsista_ic": 3, "bolsista_extensao": 3, "voluntario": 3,
                "tecnico": 4, "professor": 5, "colaborador": 6, "coordenacao": 9}
        unicos.sort(key=lambda p: (PESO.get(p[2], 5), p[1]))
        ordenados = unicos
        responsavel = ordenados[0][0]

        escrita = rng.randint(90, 430)
        submissao = inicio + timedelta(days=escrita)
        revista, issn, qualis, fi, facilidade = rng.choice(REVISTAS)
        estagio = _pick(rng, [("publicado", 0.50), ("em_producao", 0.16),
                              ("submetido", 0.09), ("em_revisao", 0.07),
                              ("aceito", 0.06), ("rejeitado", 0.12)])
        if submissao > hoje and estagio != "em_producao":
            estagio = "em_producao"

        linha_artigo: dict[str, Any] = {
            "Título": titulo,
            "Código": f"ART-{n + 1:04d}",
            "Autores": "; ".join(p[0] for p in ordenados),
            "Responsável": responsavel,
            "Linha de pesquisa": LINHAS[linha][0],
            "Tipo de estudo": _pick(rng, TIPOS_ESTUDO),
            "Idioma": _pick(rng, IDIOMAS),
            "Data de início": _iso(inicio),
            "Situação": {"em_producao": "Em produção", "submetido": "Submetido",
                         "em_revisao": "Em revisão", "aceito": "Aceito",
                         "publicado": "Publicado", "rejeitado": "Rejeitado"}[estagio],
        }
        # marcos de escrita: cada versão é um degrau até a submissão
        for i, campo in enumerate(("Primeira versão", "Segunda versão", "Terceira versão")):
            passo = inicio + timedelta(days=int(escrita * (0.30 + 0.22 * i)))
            if passo < min(hoje, submissao) and rng.random() < 0.85 - 0.15 * i:
                linha_artigo[campo] = _iso(passo)
        if estagio != "em_producao":
            linha_artigo["Versão final"] = _iso(submissao - timedelta(days=rng.randint(3, 25)))
            linha_artigo["Revisão interna"] = _iso(submissao - timedelta(days=rng.randint(10, 45)))
            linha_artigo["Data de submissão"] = _iso(submissao)
            linha_artigo["Revista submetida"] = revista
            linha_artigo["ISSN"] = issn

        # tentativas: as recusadas vêm antes, com motivo; a última decide o destino
        tentativas = 0 if estagio == "em_producao" else 1
        if estagio in ("aceito", "publicado", "rejeitado", "em_revisao"):
            tentativas = _pick(rng, [(1, 0.44 + facilidade), (2, 0.34), (3, 0.16), (4, 0.06)])
        data_envio, revista_atual, issn_atual = submissao, revista, issn
        deste_artigo: list[dict] = []
        for tentativa in range(1, tentativas + 1):
            if data_envio > hoje:
                break                       # o envio ainda não aconteceu
            ultima = tentativa == tentativas
            espera = rng.randint(25, 190) if not ultima else rng.randint(30, 240)
            decisao_em = data_envio + timedelta(days=espera)
            if decisao_em > hoje and not ultima:
                break
            if decisao_em > hoje:
                # enviado e ainda sem parecer: é o que "Submetido" quer dizer
                decisao, decisao_em = "Em avaliação", None
            elif ultima:
                if estagio == "rejeitado":
                    decisao = "Rejeitado"
                elif estagio in ("aceito", "publicado"):
                    decisao = "Aceito"
                elif estagio == "em_revisao":
                    decisao = "Revisão solicitada"
                else:
                    decisao = "Em avaliação"
            else:
                decisao = "Desk reject" if rng.random() < 0.28 else "Rejeitado"
            if decisao == "Em avaliação" and estagio in ("aceito", "publicado", "rejeitado"):
                estagio = "submetido"       # sem parecer não há aceite nem recusa
                linha_artigo["Situação"] = "Submetido"
            recusa = decisao in ("Rejeitado", "Desk reject") and (not ultima or estagio == "rejeitado")
            deste_artigo.append({
                "Artigo": titulo, "Tentativa": tentativa, "Periódico": revista_atual,
                "ISSN": issn_atual, "Data de submissão": _iso(data_envio),
                "Decisão": decisao,
                "Data da decisão": _iso(decisao_em)
                                   if decisao_em and decisao != "Em avaliação" else None,
                "Motivo da recusa": _pick(rng, [(m[0], 3.0 if i < 4 else 1.0)
                                                for i, m in enumerate(MOTIVOS)]) if recusa else None,
                "Rodadas": 0 if decisao == "Desk reject" else rng.randint(1, 3),
                "Desk reject": "Sim" if decisao == "Desk reject" else "Não",
            })
            if ultima or not decisao_em:
                break
            # ressubmissão: o laboratório leva alguns dias para reescrever e reenviar
            data_envio = decisao_em + timedelta(days=rng.randint(6, 70))
            revista_atual, issn_atual, _, _, facilidade = rng.choice(REVISTAS)
            if data_envio > hoje:
                break
        # Nenhum manuscrito fica dois anos "em avaliacao": ou sai parecer, ou o
        # laboratorio desiste e recomeca em outro lugar. Sem este corte, o sorteio
        # deixava artigos submetidos em 2020 parados no estagio, e o mural
        # anunciava "sem resposta ha 2427 dias" -- que nao e um prazo em aberto,
        # e uma pendencia que a geracao esqueceu de encerrar.
        if estagio in ("submetido", "em_revisao") and deste_artigo:
            ultimo = deste_artigo[-1]
            enviado = date.fromisoformat(ultimo["Data de submissão"])
            if (hoje - enviado).days > ESPERA_MAXIMA:
                ultimo["Decisão"] = "Rejeitado"
                ultimo["Data da decisão"] = _iso(
                    enviado + timedelta(days=rng.randint(30, 240)))
                ultimo["Motivo da recusa"] = _pick(
                    rng, [(m[0], 3.0 if i < 4 else 1.0) for i, m in enumerate(MOTIVOS)])
                estagio = "rejeitado"
                linha_artigo["Situação"] = "Rejeitado"

        submissoes.extend(deste_artigo)

        ultima_decisao = deste_artigo[-1] if deste_artigo else None
        if ultima_decisao and not ultima_decisao["Data da decisão"]:
            ultima_decisao = None           # ainda em avaliação: sem aceite nem recusa
        # sem tentativa registrada não há aceite nem recusa: o artigo volta a ser
        # manuscrito em escrita, e o painel não mostra data que não existe
        if estagio in ("aceito", "publicado", "rejeitado") and not ultima_decisao:
            estagio = "em_producao"
            linha_artigo["Situação"] = "Em produção"
            for campo in ("Versão final", "Revisão interna", "Data de submissão",
                          "Revista submetida", "ISSN"):
                linha_artigo.pop(campo, None)
        if estagio in ("aceito", "publicado") and ultima_decisao:
            aceite = date.fromisoformat(ultima_decisao["Data da decisão"])
            linha_artigo["Data do aceite"] = _iso(aceite)
            linha_artigo["Periódico"] = ultima_decisao["Periódico"]
            linha_artigo["ISSN"] = ultima_decisao["ISSN"]
            linha_artigo["Qualis"] = qualis
            linha_artigo["Fator de impacto"] = fi
            if estagio == "publicado":
                publicacao = aceite + timedelta(days=rng.randint(14, 210))
                if publicacao > hoje:
                    # aceito, mas a revista ainda não publicou: é o que "Aceito" quer dizer
                    estagio = "aceito"
                    linha_artigo["Situação"] = "Aceito"
            if estagio == "publicado":
                linha_artigo["Data de publicação"] = _iso(publicacao)
                linha_artigo["Ano"] = publicacao.year
                # 10.5555 e o prefixo que a Crossref reserva para teste: um DOI
                # assim se declara ficticio. Antes o gerador sorteava o prefixo,
                # e o DOI de mentira ficava indistinguivel de um de verdade --
                # quem clicava caia na pagina de erro do doi.org e concluia,
                # com razao, que o link do sistema estava quebrado.
                linha_artigo["DOI"] = f"10.5555/lape.{publicacao.year}.{n + 1:04d}"
                linha_artigo["Link"] = "https://doi.org/" + linha_artigo["DOI"]
                linha_artigo["Acesso aberto"] = "Sim" if rng.random() < 0.55 else "Não"
                # citações: crescem com a idade e com o peso da revista, com cauda longa
                anos_fora = max(0.25, (hoje - publicacao).days / 365)
                base = fi * anos_fora * rng.uniform(0.8, 3.4)
                if rng.random() < 0.09:
                    base *= rng.uniform(3.5, 9.0)      # o artigo que estourou
                scopus = int(base)
                linha_artigo["Citações Scopus"] = scopus
                linha_artigo["Citações WoS"] = max(0, int(scopus * rng.uniform(0.72, 0.98)))
                linha_artigo["Scopus ID"] = f"2-s2.0-{rng.randint(10**10, 10**11 - 1)}"
                linha_artigo["WoS ID"] = f"WOS:{rng.randint(10**11, 10**12 - 1)}"
                citacoes.append({
                    "titulo": titulo,
                    "openalex": max(scopus, int(scopus * rng.uniform(1.0, 1.35))),
                    "publicacao": publicacao,
                })
        elif estagio == "rejeitado" and ultima_decisao:
            linha_artigo["Motivo da recusa"] = ultima_decisao["Motivo da recusa"]

        artigos.append(linha_artigo)

    # ------------------------------------------------------------------
    # Atividades: a agenda vai de dois anos atrás até dois meses à frente
    # ------------------------------------------------------------------
    eventos = []
    dia = hoje - timedelta(days=730)
    contador = 0
    while dia < hoje + timedelta(days=70):
        dia += timedelta(days=rng.randint(2, 9))
        # dia cheio acontece: a reunião de manhã e a coleta à tarde, no mesmo dia
        for _ in range(1 if rng.random() > 0.22 else rng.randint(2, 3)):
            kind, titulo_base, local, _peso = _pick(rng, [(e, e[3]) for e in EVENTOS])
            linha = rng.randrange(len(LINHAS))
            fora = kind in ("congresso", "visita_tecnica") or rng.random() < 0.08
            inst = INSTITUICOES[rng.randrange(1, len(INSTITUICOES))] if fora else INSTITUICOES[0]
            contador += 1
            equipe = [p[0] for p in PESSOAS if p[4] == linha or rng.random() < 0.2]
            hora = rng.choice([9, 10, 14, 15, 16, 19])
            eventos.append({
                "Código": f"EV-{contador:04d}",
                "Tipo": kind,
                "Atividade": titulo_base + (f" — {LINHAS[linha][1]}" if kind != "reuniao" else ""),
                "Descrição": f"Atividade da linha {LINHAS[linha][0]}.",
                "Data": f"{_iso(dia)} {hora:02d}:00",
                "Fim": f"{_iso(dia)} {hora + rng.randint(1, 4):02d}:00",
                "Local": local, "Instituição": inst[0], "Cidade": inst[2], "Estado": inst[3],
                "País": inst[4], "Latitude": inst[5], "Longitude": inst[6],
                "Linha de pesquisa": LINHAS[linha][0],
                "Participantes": "; ".join(rng.sample(equipe, min(len(equipe), rng.randint(3, 9)))),
                "Situação": "confirmado" if dia <= hoje else "previsto",
            })

    return {
        "research_lines": linhas,
        "institutions": instituicoes,
        "rejection_reasons": motivos,
        "members": integrantes,
        "projects": projetos,
        "project_members": projeto_membros,
        "articles": artigos,
        "submissions": submissoes,
        "events": eventos,
        "_citations": citacoes,
    }


# ----------------------------------------------------------------------
# Carga: as mesmas funções que leem as planilhas de verdade
# ----------------------------------------------------------------------
def mapear(entidade: str, linhas: list[dict]) -> list[dict]:
    """Traduz cabeçalhos em português para os campos canônicos.

    É exatamente o que `rows_of()` faz ao ler uma planilha. Passar a massa por
    aqui, em vez de já entregá-la com os nomes internos, faz com que o gerador
    também exercite o mapa de sinônimos de colunas — o pedaço que costuma
    quebrar quando o laboratório renomeia uma coluna.
    """
    from .mapping import build_column_map

    if not linhas:
        return []
    cabecalhos = list(dict.fromkeys(chave for linha in linhas for chave in linha))
    mapa = build_column_map(entidade, cabecalhos)
    faltando = [c for c in cabecalhos if c not in mapa]
    if faltando:
        raise ValueError(f"colunas não reconhecidas em {entidade}: {faltando}")
    return [{campo: linha.get(original) for original, campo in mapa.items()}
            for linha in linhas]


def _historico(db, meses: int = 15, hoje: date | None = None) -> int:
    """Reconstrói o histórico medido, olhando o banco *como ele estaria* em cada data.

    Não é número inventado: cada ponto conta os registros cuja própria data já
    tinha acontecido naquele dia. É o que o lakehouse teria medido se estivesse
    rodando desde o começo — e é o que dá sentido às setas de variação.
    """
    hoje = hoje or date.today()
    marcos: list[date] = []
    for i in range(meses, 0, -1):                      # um ponto por mês
        marcos.append(hoje - timedelta(days=30 * i))
    for i in (21, 14, 7, 0):                           # e semanal no fim, para o delta de 30 dias
        marcos.append(hoje - timedelta(days=i))

    COMO_ESTAVA = {
        "artigos": "SELECT COUNT(*) FROM articles WHERE started_on <= ?",
        "publicados": "SELECT COUNT(*) FROM articles WHERE published_on <= ?",
        # em escrita = começou e ainda não tinha sido enviado naquela data
        "em_producao": ("SELECT COUNT(*) FROM articles a WHERE a.started_on <= ?"
                        " AND NOT EXISTS (SELECT 1 FROM submissions s"
                        "                 WHERE s.article_id = a.id AND s.submitted_on <= ?)"),
        # na mão da revista naquela data: enviado e ainda sem parecer, ou com
        # revisão solicitada — que é o que o painel chama de submetido + em revisão
        "submetidos": ("SELECT COUNT(DISTINCT s.article_id) FROM submissions s"
                       " WHERE s.submitted_on <= ?"
                       " AND (s.decision_on IS NULL OR s.decision_on > ?"
                       "      OR s.decision = 'revisao_solicitada')"),
        "rejeitados": ("SELECT COUNT(*) FROM submissions WHERE decision IN ('rejeitado','desk_reject')"
                       " AND decision_on <= ?"),
        "submissoes": "SELECT COUNT(*) FROM submissions WHERE submitted_on <= ?",
        # uma fonte só: somar openalex + scopus + wos contaria a mesma citação três vezes
        "citacoes": ("SELECT COALESCE(SUM(citations), 0) FROM citation_snapshots"
                     " WHERE source = 'openalex' AND snapshot_on ="
                     " (SELECT MAX(snapshot_on) FROM citation_snapshots WHERE snapshot_on <= ?)"),
        "integrantes": "SELECT COUNT(*) FROM members WHERE is_external = 0 AND joined_on <= ?",
        "projetos": "SELECT COUNT(*) FROM projects WHERE started_on <= ?",
        "atividades": "SELECT COUNT(*) FROM events WHERE start_at <= ?",
    }
    gravados = 0
    for marco in marcos:
        stamp = marco.isoformat()
        linhas = []
        for metrica, sql in COMO_ESTAVA.items():
            args = (stamp, stamp) if sql.count("?") == 2 else (stamp,)
            linhas.append((stamp, metrica, "total", "total", float(db.scalar(sql, args) or 0)))
        db.conn.executemany(
            "INSERT OR REPLACE INTO metric_snapshot"
            " (snapshot_on, metric, dimension, dim_value, value) VALUES (?, ?, ?, ?, ?)", linhas)
        gravados += len(linhas)
    db.conn.commit()
    return gravados


def _citacoes(db, massa: dict, hoje: date | None = None) -> int:
    """Escreve o que o rastreador teria encontrado: OpenAlex e a série por coleta.

    A contagem cresce de trás para frente — cada coleta anterior tem menos
    citações que a seguinte —, que é como a série se comporta na vida real.
    """
    from .util import title_key

    hoje = hoje or date.today()
    coletas = [hoje - timedelta(days=d) for d in (365, 270, 180, 120, 60, 30, 0)]
    escritos = 0
    for item in massa["_citations"]:
        row = db.dicts("SELECT id, published_on FROM articles WHERE title_key = ?",
                       (title_key(item["titulo"]),))
        if not row:
            continue
        article_id = row[0]["id"]
        atual = item["openalex"]
        db.execute("UPDATE articles SET openalex_citations = ?, citations_updated_at = ?"
                   " WHERE id = ?", (atual, hoje.isoformat(), article_id))
        publicacao = item["publicacao"]
        for coleta in coletas:
            if coleta < publicacao:
                continue
            # proporcional ao tempo decorrido desde a publicação
            fatia = (coleta - publicacao).days / max(1, (hoje - publicacao).days)
            for fonte, total in (("openalex", atual),
                                 ("scopus", int(atual * 0.82)),
                                 ("wos", int(atual * 0.74))):
                db.execute(
                    "INSERT OR REPLACE INTO citation_snapshots"
                    " (article_id, source, citations, snapshot_on) VALUES (?, ?, ?, ?)",
                    (article_id, fonte, int(round(total * min(1.0, fatia))), coleta.isoformat()))
                escritos += 1
    db.conn.commit()
    return escritos


def _achados(db, massa: dict, hoje: date | None = None) -> int:
    """Deixa alguns achados pendentes, como se o rastreador tivesse acabado de rodar."""
    from .util import title_key

    hoje = hoje or date.today()
    pendentes = [
        ("Mindfulness e regulação emocional em atletas de elite: revisão de escopo",
         "Cardoso MR; Farias TM; Pinto RS", "Psychology of Sport and Exercise", 2026),
        ("Exercise snacks e função executiva em adultos sedentários",
         "Bittencourt RN; Amaral JK", "Frontiers in Psychology", 2026),
        ("Aquatic exercise for fibromyalgia: a 24-week randomized trial",
         "Sampaio HK; Antunes LP; Hall PO", "Pain Medicine", 2025),
        ("Sedentary behaviour among public servants: a cluster analysis",
         "Cavalheiro BS; Fontanella IM", "BMC Public Health", 2026),
    ]
    for i, (titulo, autores, revista, ano) in enumerate(pendentes):
        db.upsert("discoveries", {
            "source": "openalex",
            "external_id": f"W{4300000000 + i}",
            "title": titulo,
            "authors": autores,
            "journal": revista,
            "year": ano,
            "citations": (4 - i) * 3,
            "doi": f"10.5555/demo.{ano}.{i + 1:03d}",
            "title_key": title_key(titulo),
            "url": f"https://doi.org/10.5555/demo.{ano}.{i + 1:03d}",
            "found_at": (hoje - timedelta(days=i)).isoformat(),
            "status": "pendente",
        }, conflict=("source", "title_key"))
    db.conn.commit()
    return len(pendentes)


def seed(db, seed_value: int = 20260826, n_artigos: int = 160,
         hoje: date | None = None, verbose: bool = True) -> dict[str, Any]:
    """Gera a massa e carrega no banco pelos mesmos ingestores das planilhas."""
    from . import ingest_excel, metrics

    hoje = hoje or date.today()
    massa = build(seed=seed_value, n_artigos=n_artigos, hoje=hoje)
    db.migrate()

    etapas = [
        ("linhas de pesquisa", ingest_excel.ingest_research_lines, "research_lines"),
        ("instituições", ingest_excel.ingest_institutions, "institutions"),
        ("motivos de recusa", ingest_excel.ingest_rejection_reasons, "rejection_reasons"),
        ("integrantes", ingest_excel.ingest_members, "members"),
        ("projetos", ingest_excel.ingest_projects, "projects"),
        ("equipe dos projetos", ingest_excel.ingest_project_members, "project_members"),
        ("artigos", ingest_excel.ingest_articles, "articles"),
        ("submissões", ingest_excel.ingest_submissions, "submissions"),
        ("atividades", ingest_excel.ingest_events, "events"),
    ]
    resumo: dict[str, Any] = {}
    for rotulo, funcao, chave in etapas:
        gravados = funcao(db, mapear(chave, massa[chave]))
        resumo[chave] = gravados
        db.log_ingest("massa-de-teste", target=chave, rows_read=len(massa[chave]),
                      rows_written=gravados)
        if verbose:
            print(f"  {rotulo:22} {len(massa[chave]):4} linhas -> {gravados} gravadas")

    resumo["citation_snapshots"] = _citacoes(db, massa, hoje)
    resumo["discoveries"] = _achados(db, massa, hoje)
    resumo["h_index"] = metrics.compute_h_indexes(db)
    if verbose:
        print(f"  citações                    {resumo['citation_snapshots']} medições gravadas")
        print(f"  achados pendentes           {resumo['discoveries']}")
        print(f"  índice h                    {resumo['h_index'].get('members', 0)} pesquisador(es)")
    return resumo


def run(db, seed_value: int = 20260826, n_artigos: int = 160,
        report: Path | None = None, hoje: date | None = None,
        verbose: bool = True) -> dict[str, Any]:
    """Gera a massa, monta a camada analítica, reconstrói o histórico e publica.

    O painel sai com o mesmo caminho de um dia normal de operação: ingestão,
    lakehouse, medição e publicação. A única diferença é de onde vieram as
    linhas.
    """
    from . import config, lake, metrics, report as report_mod

    hoje = hoje or date.today()
    resumo = seed(db, seed_value=seed_value, n_artigos=n_artigos, hoje=hoje, verbose=verbose)

    if verbose:
        print("  lakehouse")
    lake.ensure_schema(db)
    # a origem desta carga é o gerador, não um arquivo: é isso que a linhagem diz
    db.execute(
        "INSERT INTO lake_manifest (layer, source_path, stored_path, rows, note)"
        " VALUES ('bronze', ?, ?, ?, ?)",
        (f"lape.demo.build(seed={seed_value}, n_artigos={n_artigos})", "(em memória)",
         sum(v for v in resumo.values() if isinstance(v, int)),
         "massa de teste — dados fictícios gerados pelo próprio sistema"))
    db.conn.commit()
    resumo["gold"] = lake.build_gold(db, verbose=verbose)
    lake.take_snapshot(db, verbose=verbose)
    # A reconstrução escreve por último e inclui o ponto de hoje: a série toda
    # passa a vir do mesmo método, e não dá um salto no último ponto. O que só o
    # lakehouse mede (índice h máximo, tempo mediano, quebra por linha) fica como
    # ele gravou.
    resumo["historico"] = _historico(db, hoje=hoje)
    if verbose:
        print(f"  histórico reconstruído      {resumo['historico']} medições")

    destino = report or (config.DOCS_DIR / "demo.html")
    payload = metrics.build_payload(db)
    payload["overview"]["lab_name"] = payload["overview"]["lab_name"] + " — MASSA DE TESTE"
    html = report_mod.render(payload, destino)
    report_mod.export_json(payload, destino.with_suffix(".json"))
    resumo["painel"] = str(html)
    if verbose:
        o = payload["overview"]
        print(f"  {o['n_articles']} artigos | {o['n_published']} publicados | "
              f"{o['n_members']} integrantes | {o['n_projects']} projetos")
        print(f"  painel: {html}")
    return resumo
