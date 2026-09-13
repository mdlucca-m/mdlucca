"""Importar a planilha da bancada: participantes, medidas e itens.

Por que isto existe
  A Bancada tem onze telas e nenhum jeito de encher. Um estudo com 40
  participantes, 10 itens e 3 momentos sao 1.200 digitacoes -- ninguem
  faz, e o laboratorio ja tem tudo em Excel. Sem importador, as telas de
  correlacao, confiabilidade e poder ficam bonitas e vazias.

A regra que manda no desenho
  NUNCA GRAVA SEM CONFERIR ANTES. A funcao `ler` devolve um PLANO: o que
  entendeu de cada coluna, quantas linhas vai criar, e -- principalmente
  -- o que NAO conseguiu mapear. Quem chama olha o plano e so entao
  chama `aplicar`. Importador que grava direto e importador que estraga
  o banco em silencio, e dado de participante nao se desfaz com Ctrl+Z.

Os dois formatos que cobrem quase tudo
  LARGO   uma linha por pessoa, uma coluna por medida:
            codigo | grupo | momento | EVA | BRUMS | PSS
          ou com o momento no nome da coluna:
            codigo | grupo | EVA_base | EVA_pos | BRUMS_base | BRUMS_pos

  LONGO   uma linha por medida:
            codigo | grupo | momento | instrumento | valor

  O formato e detectado, nao perguntado -- mas a deteccao aparece no
  plano, para ser desmentida quando estiver errada.

O que este modulo se recusa a fazer
  Inventar identidade. Sem coluna de codigo do participante, ele PARA.
  Numerar as linhas 1..n pareceria funcionar e quebraria na segunda
  importacao: a mesma pessoa viraria outra, e as medidas de antes e
  depois deixariam de ser da mesma pessoa -- que e exatamente o que o
  teste pareado precisa que seja verdade.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .db import Database
from .util import clean_text, norm_key, to_float

# Como as colunas costumam se chamar. Sao PREFIXOS de chave normalizada:
# "codigo_do_participante" casa com "codigo".
NOMES_DO_CODIGO = ("codigo", "cod", "id", "participante", "sujeito", "voluntario",
                   "paciente", "registro", "matricula")
NOMES_DO_GRUPO = ("grupo", "braco", "condicao", "arm", "alocacao", "randomizacao")
NOMES_DO_MOMENTO = ("momento", "tempo", "avaliacao", "fase", "etapa", "coleta",
                    "periodo", "time", "wave")
NOMES_DO_INSTRUMENTO = ("instrumento", "escala", "questionario", "variavel",
                        "medida", "teste")
NOMES_DO_VALOR = ("valor", "resultado", "escore", "score", "nota", "pontuacao")
NOMES_DE_ITEM = ("item", "questao", "pergunta", "q")
NOMES_A_IGNORAR = ("nome", "email", "e_mail", "telefone", "celular", "cpf",
                   "endereco", "data_de_nascimento", "nascimento", "rg")

# Sufixos que denunciam o momento dentro do nome da coluna: EVA_pre, EVA_pos.
SUFIXOS_DE_MOMENTO = {
    "pre": "Pré", "pos": "Pós", "base": "Linha de base", "baseline": "Linha de base",
    "t0": "T0", "t1": "T1", "t2": "T2", "t3": "T3", "t4": "T4",
    "inicial": "Inicial", "final": "Final", "seguimento": "Seguimento",
    "followup": "Seguimento", "follow_up": "Seguimento",
}
_SUFIXO = re.compile(r"^(?P<base>.+?)_(?P<sufixo>%s)$" % "|".join(SUFIXOS_DE_MOMENTO))


class ImportError_(ValueError):
    """Erro que o usuario precisa ler, e nao um traceback."""


def ler_arquivo(caminho: Path) -> dict[str, Any]:
    """Le o arquivo e devolve {aba: linhas}, sem tocar no banco."""
    from .ingest_excel import read_source

    if not Path(caminho).exists():
        raise ImportError_("arquivo não encontrado: %s" % caminho)
    try:
        abas = read_source(Path(caminho))
    except Exception as erro:                     # pragma: no cover - depende do arquivo
        raise ImportError_("não deu para abrir a planilha: %s" % erro) from erro
    saida = {}
    for nome, frame in abas.items():
        linhas = []
        for registro in frame.to_dict(orient="records"):
            limpo = {str(k): v for k, v in registro.items()}
            if any(clean_text(v) is not None for v in limpo.values()):
                linhas.append(limpo)
        if linhas:
            saida[str(nome)] = linhas
    if not saida:
        raise ImportError_("a planilha não tem nenhuma linha preenchida")
    return saida


def ler_texto(texto: str) -> list[dict]:
    """Le o que foi COLADO da planilha.

    Copiar do Excel e colar numa caixa de texto e o caminho mais curto
    entre o dado e o sistema: nao pede arquivo no servidor, nao pede
    upload, funciona de qualquer maquina e o pesquisador ja sabe fazer.
    O Excel cola separado por TAB; aceito ponto-e-virgula e virgula
    tambem, porque e o que sai de um CSV brasileiro.
    """
    linhas_cruas = [l for l in (texto or "").splitlines() if l.strip()]
    if len(linhas_cruas) < 2:
        raise ImportError_("cole o cabeçalho e ao menos uma linha de dados")
    separador = "\t" if "\t" in linhas_cruas[0] else (
        ";" if ";" in linhas_cruas[0] else ",")
    cabecalho = [c.strip() for c in linhas_cruas[0].split(separador)]
    if len(cabecalho) < 2:
        raise ImportError_(
            "não reconheci as colunas. Copie do Excel incluindo o cabeçalho, "
            "ou separe por ponto-e-vírgula.")
    saida = []
    for crua in linhas_cruas[1:]:
        partes = crua.split(separador)
        # linha mais curta que o cabecalho e linha com celula vazia no fim,
        # e nao linha invalida: o Excel corta os tabs finais
        partes += [""] * (len(cabecalho) - len(partes))
        registro = dict(zip(cabecalho, partes[:len(cabecalho)]))
        if any(clean_text(v) is not None for v in registro.values()):
            saida.append(registro)
    if not saida:
        raise ImportError_("nenhuma linha de dados depois do cabeçalho")
    return saida


def _casa(chave: str, nomes: tuple[str, ...]) -> bool:
    return any(chave == n or chave.startswith(n + "_") for n in nomes)


def _separar_momento(chave: str) -> tuple[str, str | None]:
    """'eva_pre' -> ('eva', 'Pré'). Sem sufixo conhecido, devolve o nome cru."""
    achado = _SUFIXO.match(chave)
    if not achado:
        return chave, None
    return achado.group("base"), SUFIXOS_DE_MOMENTO[achado.group("sufixo")]


def entender(linhas: list[dict]) -> dict[str, Any]:
    """O que cada coluna parece ser. Devolve a LEITURA, sem decidir nada."""
    colunas = list(linhas[0].keys())
    papeis: dict[str, dict] = {}
    for coluna in colunas:
        chave = norm_key(coluna)
        valores = [linha.get(coluna) for linha in linhas]
        numericos = sum(1 for v in valores if to_float(v) is not None)
        papel = "medida"
        if _casa(chave, NOMES_A_IGNORAR):
            papel = "ignorada"
        elif _casa(chave, NOMES_DO_CODIGO):
            papel = "codigo"
        elif _casa(chave, NOMES_DO_GRUPO):
            papel = "grupo"
        elif _casa(chave, NOMES_DO_MOMENTO):
            papel = "momento"
        elif _casa(chave, NOMES_DO_INSTRUMENTO):
            papel = "instrumento"
        elif _casa(chave, NOMES_DO_VALOR):
            papel = "valor"
        elif numericos == 0:
            # coluna sem nenhum numero nao e medida; pode ser observacao
            papel = "ignorada"
        base, momento = _separar_momento(chave) if papel == "medida" else (chave, None)
        # O nome que vai para a tela e o TEXTO da coluna, nao a chave
        # normalizada: "EVA" declarado como "eva" apareceria assim em todo
        # relatorio, e o pesquisador nao reconhece o proprio instrumento.
        rotulo = str(coluna).strip()
        if momento:
            rotulo = re.sub(r"[ _-]*%s\s*$" % re.escape(rotulo.split("_")[-1]),
                            "", rotulo).strip(" _-") or base
        papeis[coluna] = {
            "coluna": coluna, "papel": papel, "chave": chave,
            "instrumento": rotulo if papel == "medida" else None,
            "momento_no_nome": momento,
            "numericos": numericos, "preenchidas": sum(
                1 for v in valores if clean_text(v) is not None),
        }
    return papeis


def _formato(papeis: dict[str, dict]) -> str:
    tem_instrumento = any(p["papel"] == "instrumento" for p in papeis.values())
    tem_valor = any(p["papel"] == "valor" for p in papeis.values())
    return "longo" if (tem_instrumento and tem_valor) else "largo"


def planejar(linhas: list[dict], protocolo: str | None = None) -> dict[str, Any]:
    """Le a planilha e devolve o PLANO: o que sera criado, e o que sobrou.

    Nada aqui toca o banco. O plano existe para ser olhado antes.
    """
    papeis = entender(linhas)
    formato = _formato(papeis)
    do_papel = lambda nome: [c for c, p in papeis.items() if p["papel"] == nome]  # noqa: E731

    codigos = do_papel("codigo")
    if not codigos:
        raise ImportError_(
            "nenhuma coluna identifica o participante. Uma delas precisa se chamar "
            "'codigo', 'participante', 'sujeito' ou parecido — sem isso, a mesma "
            "pessoa viraria outra na próxima importação, e o antes e depois "
            "deixariam de ser da mesma pessoa.")
    col_codigo = codigos[0]
    col_grupo = (do_papel("grupo") or [None])[0]
    col_momento = (do_papel("momento") or [None])[0]

    medidas: list[dict] = []
    problemas: list[str] = []
    participantes: dict[str, dict] = {}
    instrumentos: set[str] = set()
    # dict, e nao set: a ORDEM DE APARICAO na planilha e informacao, e e
    # a melhor que existe para momento lido de uma coluna
    momentos: dict[str, None] = {}
    momento_do_sufixo: set[str] = set()

    for numero, linha in enumerate(linhas, start=2):     # 1 e o cabecalho
        codigo = clean_text(linha.get(col_codigo))
        if not codigo:
            problemas.append("linha %d: sem código de participante — ignorada" % numero)
            continue
        grupo = clean_text(linha.get(col_grupo)) if col_grupo else None
        participantes.setdefault(codigo, {"codigo": codigo, "grupo": grupo})
        momento_da_linha = clean_text(linha.get(col_momento)) if col_momento else None

        if formato == "longo":
            nome = clean_text(linha.get(do_papel("instrumento")[0]))
            bruto = linha.get(do_papel("valor")[0])
            valor = to_float(bruto)
            if not nome:
                problemas.append("linha %d: sem instrumento — ignorada" % numero)
                continue
            if valor is None:
                problemas.append("linha %d, %s: valor %r não é número — ignorado"
                                 % (numero, nome, clean_text(bruto)))
                continue
            instrumentos.add(nome)
            if momento_da_linha:
                momentos.setdefault(momento_da_linha, None)
            medidas.append({"codigo": codigo, "instrumento": nome,
                            "momento": momento_da_linha, "valor": valor})
            continue

        for coluna, papel in papeis.items():
            if papel["papel"] != "medida":
                continue
            bruto = linha.get(coluna)
            if clean_text(bruto) is None:
                continue
            valor = to_float(bruto)
            nome = papel["instrumento"]
            momento = papel["momento_no_nome"] or momento_da_linha
            if valor is None:
                problemas.append("linha %d, coluna %s: %r não é número — ignorado"
                                 % (numero, coluna, clean_text(bruto)))
                continue
            instrumentos.add(nome)
            if momento:
                momentos.setdefault(momento, None)
                if papel["momento_no_nome"]:
                    momento_do_sufixo.add(momento)
            medidas.append({"codigo": codigo, "instrumento": nome,
                            "momento": momento, "valor": valor})

    # A ordem dos momentos decide o que e "antes" e o que e "depois" no
    # grafico e no teste pareado. Duas origens, duas regras:
    #
    #   · veio de um SUFIXO de coluna (EVA_pre, EVA_pos) -- a ordem e
    #     conhecida, porque fui eu que reconheci o sufixo;
    #   · veio de uma COLUNA de momento -- eu nao sei a ordem, e nao vou
    #     fingir que sei. Fica a ordem de aparicao na planilha, que e a do
    #     pesquisador. Ordenar por alfabeto poria "Final" antes de "Base"
    #     e inverteria o estudo -- e foi o que aconteceu quando tentei
    #     aplicar a cronologia a nomes que ela nao conhece.
    if momento_do_sufixo and momento_do_sufixo >= set(momentos):
        cronologia = {r: i for i, r in enumerate(SUFIXOS_DE_MOMENTO.values())}
        em_ordem = sorted(momentos, key=lambda n: (cronologia.get(n, 999), n))
    else:
        em_ordem = list(momentos)

    return {
        "formato": formato,
        "protocolo": protocolo,
        "colunas": list(papeis.values()),
        "coluna_codigo": col_codigo,
        "coluna_grupo": col_grupo,
        "coluna_momento": col_momento,
        "participantes": sorted(participantes.values(), key=lambda p: p["codigo"]),
        "instrumentos": sorted(instrumentos),
        "momentos": em_ordem,
        # de onde veio a ordem -- para a tela poder dizer "confira" quando
        # ela e so a ordem em que as linhas apareceram
        "ordem_dos_momentos": ("sufixo das colunas"
                               if momento_do_sufixo and momento_do_sufixo >= set(momentos)
                               else "ordem de aparição na planilha"),
        "medidas": medidas,
        "n_medidas": len(medidas),
        "problemas": problemas,
        "ignoradas": [p["coluna"] for p in papeis.values() if p["papel"] == "ignorada"],
        # Quanto falta em cada coluna de medida. O leitor de planilha
        # converte "n/a", "NA" e afins em celula vazia ANTES de o
        # importador ver, entao nao da para reclamar de cada uma -- mas da
        # para dizer que a coluna esta pela metade, que e o que importa
        # para quem vai analisar.
        "preenchimento": [
            {"coluna": p["coluna"], "instrumento": p["instrumento"],
             "preenchidas": p["preenchidas"], "linhas": len(linhas),
             "faltam": len(linhas) - p["preenchidas"]}
            for p in papeis.values() if p["papel"] == "medida"],
    }


def conferir(db: Database, plano: dict, protocolo_id: int) -> dict[str, Any]:
    """O que ja existe e o que sera criado -- ainda sem gravar nada.

    A diferenca entre "criar" e "atualizar" e o que decide se a pessoa
    aperta o botao. Importar por cima de um estudo em andamento e
    diferente de importar num vazio, e o plano tem de dizer qual dos
    dois e ANTES.
    """
    from . import coleta

    ja_inscritos = {p["codigo"]: p for p in coleta.participantes(db, protocolo_id)}
    ja_declarados = {i["nome"].strip().lower(): i for i in coleta.instrumentos(db, True)}
    momentos = {m["nome"].strip().lower(): m for m in db.dicts(
        "SELECT * FROM momentos WHERE protocolo_id = ?", (protocolo_id,))}

    novos_p = [p for p in plano["participantes"] if p["codigo"] not in ja_inscritos]
    novos_i = [n for n in plano["instrumentos"] if n.strip().lower() not in ja_declarados]
    novos_m = [n for n in plano["momentos"] if n.strip().lower() not in momentos]

    # Medida que ja existe sera SOBRESCRITA, e isso precisa aparecer antes:
    # e a diferenca entre "carregar" e "corrigir".
    existentes = 0
    if ja_inscritos and ja_declarados:
        for m in plano["medidas"]:
            p = ja_inscritos.get(m["codigo"])
            i = ja_declarados.get(m["instrumento"].strip().lower())
            mo = momentos.get((m["momento"] or "").strip().lower()) if m["momento"] else None
            if not p or not i:
                continue
            if db.dicts(
                "SELECT 1 FROM coletas WHERE participante_id = ? AND instrumento_id = ?"
                "  AND COALESCE(momento_id, -1) = COALESCE(?, -1) AND subescala IS NULL",
                    (p["id"], i["id"], mo["id"] if mo else None)):
                existentes += 1

    return {
        **plano,
        "protocolo_id": protocolo_id,
        "participantes_novos": len(novos_p),
        "participantes_existentes": len(plano["participantes"]) - len(novos_p),
        "instrumentos_novos": novos_i,
        "momentos_novos": novos_m,
        "medidas_a_sobrescrever": existentes,
        "medidas_a_criar": plano["n_medidas"] - existentes,
    }


def aplicar(db: Database, plano: dict, protocolo_id: int,
            criar_faltantes: bool = True) -> dict[str, Any]:
    """Grava o plano. So deve ser chamado depois de `conferir`.

    `criar_faltantes=False` recusa a importacao quando ela criaria
    instrumento ou momento que ninguem declarou -- e o modo para quem ja
    tem o protocolo montado e nao quer que um erro de digitacao no
    cabecalho vire um instrumento novo chamado "EVAA".
    """
    from . import coleta

    conferido = conferir(db, plano, protocolo_id)
    if not criar_faltantes:
        faltando = conferido["instrumentos_novos"] + conferido["momentos_novos"]
        if faltando:
            raise ImportError_(
                "a planilha traz o que não está declarado: %s. Declare antes, ou "
                "importe com 'criar_faltantes'." % ", ".join(faltando))

    por_codigo = {p["codigo"]: p for p in coleta.participantes(db, protocolo_id)}
    for pessoa in plano["participantes"]:
        if pessoa["codigo"] in por_codigo:
            continue
        por_codigo[pessoa["codigo"]] = coleta.inscrever(
            db, pessoa["codigo"], protocolo_id, grupo=pessoa.get("grupo"))

    por_nome = {i["nome"].strip().lower(): i for i in coleta.instrumentos(db, True)}
    for nome in plano["instrumentos"]:
        if nome.strip().lower() in por_nome:
            continue
        por_nome[nome.strip().lower()] = coleta.declarar_instrumento(
            db, norm_key(nome)[:40] or "inst", nome)

    momentos = {m["nome"].strip().lower(): m for m in db.dicts(
        "SELECT * FROM momentos WHERE protocolo_id = ?", (protocolo_id,))}
    for ordem, nome in enumerate(plano["momentos"], start=len(momentos) + 1):
        if nome.strip().lower() in momentos:
            continue
        momentos[nome.strip().lower()] = coleta.declarar_momento(
            db, protocolo_id, norm_key(nome)[:30] or ("m%d" % ordem), nome, ordem)

    gravadas = 0
    for m in plano["medidas"]:
        pessoa = por_codigo.get(m["codigo"])
        instrumento = por_nome.get(m["instrumento"].strip().lower())
        if not pessoa or not instrumento:
            continue
        momento = momentos.get((m["momento"] or "").strip().lower()) if m["momento"] else None
        coleta.registrar(db, pessoa["id"], instrumento["id"], m["valor"],
                         momento["id"] if momento else None)
        gravadas += 1

    db.log_ingest("bancada", target="coletas", rows_written=gravadas,
                  message="importação: %d participante(s), %d medida(s)"
                          % (len(plano["participantes"]), gravadas))
    return {
        "participantes": len(plano["participantes"]),
        "instrumentos": len(plano["instrumentos"]),
        "momentos": len(plano["momentos"]),
        "medidas": gravadas,
        "problemas": plano["problemas"],
    }
