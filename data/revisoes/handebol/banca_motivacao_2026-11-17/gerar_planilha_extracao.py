"""Planilha de extração (xlsx) dos estudos de motivação com texto completo.

    python3 gerar_planilha_extracao.py <pasta_json> <saida.xlsx>

Lê os JSON de extração (grupo_A/B/C.json), une num só arquivo `extracao_textos_completos.json` ao lado do xlsx e gera
a planilha com links para o site de publicação (DOI) e para o PDF local.
"""
import glob
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

PASTA_JSON, SAIDA = Path(sys.argv[1]), Path(sys.argv[2])
AQUI = SAIDA.parent
REG = []
for f in sorted(glob.glob(str(PASTA_JSON / "grupo_*.json"))):
    REG += json.load(open(f, encoding="utf-8"))
for r in REG:
    r.setdefault("fonte_extracao", "Texto completo (leitura integral)")
for f in sorted(glob.glob(str(AQUI / "json_sem_texto" / "grupo_*.json"))):
    for r in json.load(open(f, encoding="utf-8")):
        r["fonte_extracao"] = "Somente resumo e extração da revisão de mapeamento (texto completo não obtido)"
        REG.append(r)
REG.sort(key=lambda r: int(r["id"]))
json.dump(REG, open(AQUI / "extracao_37_estudos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# link do site de publicação quando o artigo não tem DOI
URL_SEM_DOI = {"014": "https://dialnet.unirioja.es/servlet/articulo?codigo=3638892",
               "053": "https://dialnet.unirioja.es/servlet/articulo?codigo=6092463",
               "055": "https://dialnet.unirioja.es/servlet/articulo?codigo=6291279",
               "104": "https://dialnet.unirioja.es/servlet/articulo?codigo=8039670",
               "105": "https://recyt.fecyt.es/index.php/JSHR/article/view/91215",
               "022": "https://dialnet.unirioja.es/servlet/articulo?codigo=3743176",
               "023": "https://dialnet.unirioja.es/servlet/articulo?codigo=6928161"}
DOI_CONHECIDO = {"006": "10.1002/ejsp.98", "012": "10.47197/retos.v0i16.34967", "021": "10.5232/ricyde2011.02503",
                 "026": "10.1016/j.psychsport.2012.08.001", "049": "10.3389/fpsyg.2017.02081",
                 "060": "10.3390/ijerph16010078", "070": "10.3390/ijerph16152702", "080": "10.3390/ijerph16030344",
                 "087": "10.3390/ijerph17020592", "100": "10.1344/anpsic2021.51/3.18", "118": "10.5114/hm.2023.116531",
                 "128": "10.47197/retos.v43i0.89294", "137": "10.17309/tmfv.2023.3.17",
                 "149": "10.1177/17479541231223652", "164": "10.3390/sports13120421",
                 "171": "10.17979/sportis.2025.11.4.11990", "184": "10.21203/rs.3.rs-8338987/v1",
                 "187": "10.3389/fspor.2026.1827113", "196": "10.3389/fpsyg.2026.1902591"}
PDFS = {p.name[:3]: p.name for p in sorted((AQUI / "textos_completos").glob("*.pdf")) if "pdf_original" not in p.name}


def doi_de(r):
    d = (r.get("doi") or "").strip().replace("https://doi.org/", "").replace("doi:", "").strip()
    if not d or d.lower().startswith("não"):
        d = DOI_CONHECIDO.get(r["id"], "")
    return d


CAMPOS = [("id", "Nº"), ("autores", "Autores"), ("ano", "Ano"), ("titulo", "Título"), ("revista", "Revista"),
          ("volume", "Volume"), ("numero", "Número"), ("paginas", "Páginas"), ("doi", "DOI"),
          ("link", "Link da publicação"), ("pdf", "Texto completo (arquivo)"), ("fonte_extracao", "Fonte da extração"), ("idioma", "Idioma"),
          ("pais_amostra", "País da amostra"), ("objetivo", "Objetivo"), ("hipoteses", "Hipóteses"),
          ("referencial_teorico", "Referencial teórico"), ("delineamento", "Delineamento"),
          ("momento_local_coleta", "Momento e local da coleta"), ("amostragem_recrutamento", "Amostragem e recrutamento"),
          ("criterios_inclusao_exclusao", "Critérios de inclusão e exclusão"), ("n_total", "n total"),
          ("n_analisado", "n analisado e perdas"), ("n_por_grupo", "n por grupo"), ("sexo", "Sexo"), ("idade", "Idade"),
          ("categoria_nivel", "Categoria e nível"), ("experiencia_treino", "Experiência e treino"),
          ("modalidades", "Modalidades"), ("variaveis_tad", "Variáveis da TAD"), ("outras_variaveis", "Outras variáveis"),
          ("instrumentos", "Instrumentos"), ("confiabilidade_amostra", "Confiabilidade na amostra"),
          ("validade_fatorial", "Validade fatorial"), ("intervencao", "Intervenção"), ("grupo_controle", "Grupo controle"),
          ("analise_estatistica", "Análise estatística"), ("resultados_principais", "Resultados principais"),
          ("resultados_tad", "Resultados da TAD"), ("conclusao_autores", "Conclusão dos autores"),
          ("limitacoes_autores", "Limitações declaradas"), ("aplicacoes_praticas", "Aplicações práticas"),
          ("etica_consentimento", "Ética e consentimento"), ("financiamento_conflitos", "Financiamento e conflitos"),
          ("problemas_identificados", "Problemas identificados na leitura"),
          ("sobreposicao_amostra", "Sobreposição de amostra"), ("observacoes", "Observações")]
LARG = {"id": 6, "autores": 30, "ano": 7, "titulo": 45, "revista": 25, "volume": 8, "numero": 8, "paginas": 10,
        "doi": 28, "link": 32, "pdf": 32, "idioma": 10, "pais_amostra": 18}

AZUL = PatternFill("solid", fgColor="1F3B57")
CINZA = PatternFill("solid", fgColor="F4F6F9")
FINO = Side(style="thin", color="BFBFBF")
BORDA = Border(left=FINO, right=FINO, top=FINO, bottom=FINO)
LINK = Font(name="Calibri", size=10, color="0563C1", underline="single")

wb = Workbook()
ws = wb.active
ws.title = "Extração completa"
AMARELO = PatternFill("solid", fgColor="FFF4CE")
for j, (_, rot) in enumerate(CAMPOS, 1):
    c = ws.cell(row=1, column=j, value=rot)
    c.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    c.fill = AZUL
    c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    c.border = BORDA
    ws.column_dimensions[get_column_letter(j)].width = LARG.get(CAMPOS[j - 1][0], 45)
ws.row_dimensions[1].height = 32
for i, r in enumerate(REG, 2):
    doi = doi_de(r)
    url = f"https://doi.org/{doi}" if doi else URL_SEM_DOI.get(r["id"], "")
    for j, (k, _) in enumerate(CAMPOS, 1):
        if k == "doi":
            v = doi or "não relatado"
        elif k == "link":
            v = url or "não localizado"
        elif k == "pdf":
            v = PDFS.get(r["id"], "")
        else:
            v = r.get(k, "")
            if isinstance(v, (list, dict)):
                v = json.dumps(v, ensure_ascii=False)
        c = ws.cell(row=i, column=j, value=str(v))
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.font = Font(name="Calibri", size=10)
        c.border = BORDA
        if not PDFS.get(r["id"]):
            c.fill = AMARELO
        elif i % 2:
            c.fill = CINZA
        if k == "link" and url:
            c.hyperlink, c.font = url, LINK
        if k == "titulo" and url:
            c.hyperlink, c.font = url, LINK
        if k == "pdf" and v:
            c.hyperlink, c.font = f"textos_completos/{v}", LINK
    ws.row_dimensions[i].height = 230
ws.freeze_panes = "E2"
ws.auto_filter.ref = ws.dimensions

# resumo
rs = wb.create_sheet("Resumo")
CAB = ["Nº", "Estudo", "Revista", "Link da publicação", "Fonte da extração", "País", "n", "Idade", "Delineamento", "Variáveis da TAD",
       "Problemas identificados"]
LR = [6, 34, 28, 34, 24, 16, 26, 26, 26, 40, 70]
for j, (t, w) in enumerate(zip(CAB, LR), 1):
    c = rs.cell(row=1, column=j, value=t)
    c.font, c.fill, c.border = Font(bold=True, color="FFFFFF", size=10), AZUL, BORDA
    c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    rs.column_dimensions[get_column_letter(j)].width = w
for i, r in enumerate(REG, 2):
    doi = doi_de(r)
    url = f"https://doi.org/{doi}" if doi else URL_SEM_DOI.get(r["id"], "")
    aut = r.get("autores", "").split(";")[0].split(",")[0].strip()
    nome = f"{aut}{' et al.' if r.get('autores', '').count(';') >= 1 else ''} ({r.get('ano', '')})"
    vals = [r["id"], nome, r.get("revista", ""), url, r.get("fonte_extracao", ""), r.get("pais_amostra", ""), r.get("n_analisado", ""),
            r.get("idade", ""), r.get("delineamento", ""), r.get("variaveis_tad", ""), r.get("problemas_identificados", "")]
    for j, v in enumerate(vals, 1):
        c = rs.cell(row=i, column=j, value=str(v))
        c.alignment, c.font, c.border = Alignment(wrap_text=True, vertical="top"), Font(size=10), BORDA
        if j == 4 and url:
            c.hyperlink, c.font = url, LINK
    rs.row_dimensions[i].height = 120
rs.freeze_panes = "C2"

# campos
cs = wb.create_sheet("Campos e notas")
NOTAS = [("Fonte", "Leitura integral dos textos completos de acesso aberto guardados em textos_completos/. Somente o que "
                   "o texto afirma; 'não relatado' quando a informação não aparece."),
         ("Links", "A coluna 'Link da publicação' e o título levam ao site da revista pelo DOI (ou à página do artigo, "
                   "quando não há DOI). A coluna 'Texto completo (arquivo)' abre o PDF local, desde que a planilha esteja "
                   "na mesma pasta que a subpasta textos_completos."),
         ("Versões", "149 é o manuscrito dos autores (Zenodo); 026 é a versão dos autores (Universidade de Birmingham); "
                     "184 é preprint (Research Square); 060, 070, 080, 087 e 164 vieram do texto completo do Europe PMC."),
         ("Problemas identificados", "Inclui inconsistências entre resumo, texto e tabelas e verificações "
                                     "aritméticas feitas na leitura, sinalizadas como cálculo de verificação."),
         ("Estudos sem texto completo", "As 13 linhas em amarelo (5, 7, 8, 9, 20, 22, 23, 36, 79, 99, 125, 160 e 185) "
                                       "foram preenchidas só com o resumo publicado e a extração da revisão de mapeamento, "
                                       "porque o texto completo não foi obtido em acesso aberto. Os campos ausentes dizem "
                                       "'não relatado no resumo'."),
         ("TAD", "Teoria da autodeterminação.")]
for i, (a, b) in enumerate(NOTAS, 1):
    cs.cell(row=i, column=1, value=a).font = Font(bold=True)
    c = cs.cell(row=i, column=2, value=b)
    c.alignment = Alignment(wrap_text=True, vertical="top")
cs.column_dimensions["A"].width = 26
cs.column_dimensions["B"].width = 120
wb.save(SAIDA)
print("ok", SAIDA, len(REG))
