# -*- coding: utf-8 -*-
"""Gera um projeto Power BI (PBIP, formato aberto em texto) a partir do
BRUMS_HIIT_PowerBI.xlsx: modelo semântico em TMDL (tabelas, tipos, parâmetro
de pasta, relações e algumas medidas) e um relatório mínimo (uma página).

IMPORTANTE (integridade): este é um SCAFFOLD gerado por código, não testado no
Power BI Desktop. Abra a pasta pelo Power BI Desktop, ajuste o parâmetro
`PastaDados` para a pasta deste projeto e monte os visuais conforme o
GUIA_POWERBI.md. O caminho 100% confiável é: importar o Excel e colar as
medidas de medidas_DAX.txt.

Uso: python build_pbip.py  (de dentro de powerbi/)"""
import os, json, uuid
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(HERE, 'BRUMS_HIIT_PowerBI.xlsx')
PROJ = 'BRUMS_HIIT'
SM = os.path.join(HERE, f'{PROJ}.SemanticModel')
RP = os.path.join(HERE, f'{PROJ}.Report')
os.makedirs(os.path.join(SM, 'definition', 'tables'), exist_ok=True)
os.makedirs(RP, exist_ok=True)

def w(path, txt):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(txt)

def tmdl_type(dt):
    k = dt.kind
    if k in ('i', 'u'): return 'int64'
    if k == 'f': return 'double'
    if k == 'b': return 'boolean'
    return 'string'

def m_type(dt):
    k = dt.kind
    if k in ('i', 'u'): return 'Int64.Type'
    if k == 'f': return 'type number'
    if k == 'b': return 'type logical'
    return 'type text'

xls = pd.ExcelFile(XLSX)
sheets = xls.sheet_names

# ---------------- .platform files ----------------
def platform(kind):
    return json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": kind, "displayName": PROJ},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}
    }, ensure_ascii=False, indent=2)

w(os.path.join(SM, '.platform'), platform('SemanticModel'))
w(os.path.join(RP, '.platform'), platform('Report'))

# ---------------- .pbip ----------------
w(os.path.join(HERE, f'{PROJ}.pbip'), json.dumps({
    "version": "1.0",
    "artifacts": [{"report": {"path": f"{PROJ}.Report"}}],
    "settings": {"enableAutoRecovery": True}
}, ensure_ascii=False, indent=2))

# ---------------- SemanticModel/definition.pbism ----------------
w(os.path.join(SM, 'definition.pbism'), json.dumps({"version": "4.0", "settings": {}}, indent=2))

# ---------------- database.tmdl ----------------
w(os.path.join(SM, 'definition', 'database.tmdl'), "database\n\tcompatibilityLevel: 1567\n")

# ---------------- expressions.tmdl (parâmetro PastaDados) ----------------
expr = ('expression PastaDados = "' + HERE.replace('\\', '\\\\') + '" meta '
        '[IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
        '\tlineageTag: ' + str(uuid.uuid4()) + '\n')
w(os.path.join(SM, 'definition', 'expressions.tmdl'), expr)

# ---------------- model.tmdl ----------------
model = ("model Model\n\tculture: pt-BR\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
         "\tsourceQueryCulture: pt-BR\n\n"
         "\tannotation __PBI_Scaffold = gerado por build_pbip.py — abrir/validar no Power BI Desktop\n\n"
         "ref expression PastaDados\n" + "".join(f"ref table {s}\n" for s in sheets))
w(os.path.join(SM, 'definition', 'model.tmdl'), model)

# ---------------- tables/*.tmdl ----------------
# medidas simples e robustas embutidas em fato_humor
MEASURES = {
    'fato_humor': [
        ("Observações", "COUNTROWS ( fato_humor )", "#,0"),
        ("Atletas", "DISTINCTCOUNT ( fato_humor[atleta] )", "#,0"),
        ("Média PTH", "AVERAGE ( fato_humor[PTH] )", "0.00"),
    ],
    'resposta_aguda': [
        ("dz Fadiga física", "CALCULATE ( SELECTEDVALUE ( resposta_aguda[dz] ), resposta_aguda[codigo] = \"FadFis\" )", "0.00"),
    ],
    'roc_prepos': [
        ("AUC Fadiga física", "CALCULATE ( SELECTEDVALUE ( roc_prepos[AUC] ), roc_prepos[codigo] = \"FadFis\" )", "0.00"),
    ],
}

for s in sheets:
    df = xls.parse(s, nrows=200)
    lines = [f"table {s}", f"\tlineageTag: {uuid.uuid4()}", ""]
    # measures
    for name, expr_dax, fmt in MEASURES.get(s, []):
        lines.append(f"\tmeasure '{name}' = {expr_dax}")
        lines.append(f"\t\tformatString: {fmt}")
        lines.append(f"\t\tlineageTag: {uuid.uuid4()}")
        lines.append("")
    # columns
    for col in df.columns:
        dt = df[col].dtype
        lines.append(f"\tcolumn '{col}'")
        lines.append(f"\t\tdataType: {tmdl_type(dt)}")
        lines.append(f"\t\tsourceColumn: {col}")
        lines.append(f"\t\tlineageTag: {uuid.uuid4()}")
        if tmdl_type(dt) in ('int64', 'double'):
            lines.append("\t\tsummarizeBy: none")
        lines.append("")
    # partition (M / Power Query importando a aba do Excel)
    type_map = ", ".join(f'{{"{c}", {m_type(df[c].dtype)}}}' for c in df.columns)
    m = [
        f"\tpartition {s} = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\tlet",
        "\t\t\t    Fonte = Excel.Workbook(File.Contents(PastaDados & \"\\BRUMS_HIIT_PowerBI.xlsx\"), null, true),",
        f"\t\t\t    Nav = Fonte{{[Item=\"{s}\",Kind=\"Sheet\"]}}[Data],",
        "\t\t\t    Cab = Table.PromoteHeaders(Nav, [PromoteAllScalars=true]),",
        f"\t\t\t    Tipos = Table.TransformColumnTypes(Cab, {{{type_map}}})",
        "\t\t\tin",
        "\t\t\t    Tipos",
        "",
    ]
    lines += m
    w(os.path.join(SM, 'definition', 'tables', f'{s}.tmdl'), "\n".join(lines))

# ---------------- relationships.tmdl ----------------
rel = (
    f"relationship {uuid.uuid4()}\n\tfromColumn: fato_humor.dia\n\ttoColumn: dim_dia.dia\n\n"
    f"relationship {uuid.uuid4()}\n\tfromColumn: fato_humor.momento\n\ttoColumn: dim_momento.momento\n"
)
w(os.path.join(SM, 'definition', 'relationships.tmdl'), rel)

# ---------------- Report/definition.pbir ----------------
w(os.path.join(RP, 'definition.pbir'), json.dumps({
    "version": "4.0",
    "datasetReference": {"byPath": {"path": f"../{PROJ}.SemanticModel"}}
}, ensure_ascii=False, indent=2))

# ---------------- Report/report.json (uma página em branco) ----------------
cfg = {"version": "5.43", "themeCollection": {"baseTheme": {"name": "CY24SU10"}}}
page = {
    "name": str(uuid.uuid4()), "displayName": "Visão geral",
    "displayOption": 1, "width": 1280, "height": 720, "visualContainers": []
}
report = {
    "config": json.dumps(cfg, ensure_ascii=False),
    "layoutOptimization": 0,
    "sections": [page],
    "publicCustomVisuals": [],
    "resourcePackages": []
}
w(os.path.join(RP, 'report.json'), json.dumps(report, ensure_ascii=False, indent=2))

print('PBIP gerado:')
for root, _, files in os.walk(SM):
    for f in files:
        print('  ', os.path.relpath(os.path.join(root, f), HERE))
for root, _, files in os.walk(RP):
    for f in files:
        print('  ', os.path.relpath(os.path.join(root, f), HERE))
print('  ', f'{PROJ}.pbip')
