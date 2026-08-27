"""Dicionário controlado de instrumentos psicométricos e famílias de construto.

Responde ao achado B5 da revisão: o campo `instrumentos` da biblioteca lista
todos os instrumentos do artigo — teste de agilidade, CMJ, DXA, lactímetro —
de modo que a "Tabela 5 de instrumentos psicométricos" não continha
instrumentos psicométricos. Aqui o instrumento psicométrico é *detectado* por
dicionário, e a família de construto é atribuída pelo instrumento efetivamente
aferido, não pela marcação de família no nível do artigo (achado B4).

Cada entrada declara:
    canonico   nome do instrumento como deve aparecer na tabela
    familia    família de construto da Tabela 4
    padroes    expressões regulares aplicadas a título+resumo+palavras-chave
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Famílias de construto, na ordem da Tabela 4 do manuscrito.
FAMILIAS = [
    "ansiedade e estresse", "motivação", "cognição e atenção",
    "burnout e saúde mental", "coping e resiliência", "sono e recuperação",
    "autoeficácia e confiança", "humor e afeto", "personalidade",
    "coesão e grupo", "emoção",
]


@dataclass(frozen=True)
class Instrumento:
    canonico: str
    familia: str
    padroes: tuple[str, ...]


def _i(canonico: str, familia: str, *padroes: str) -> Instrumento:
    assert familia in FAMILIAS, familia
    return Instrumento(canonico, familia, padroes)


# ── Dicionário ──────────────────────────────────────────────────────────────
# Os padrões são aplicados a um texto já rebaixado a minúsculas e sem
# diacríticos. \b evita casar "poms" dentro de outra palavra.
INSTRUMENTOS: tuple[Instrumento, ...] = (
    # ansiedade e estresse
    _i("CSAI-2 / CSAI-2R", "ansiedade e estresse",
       r"\bcsai[- ]?2r?\b", r"competitive state anxiety inventory"),
    _i("SAS / SAS-2", "ansiedade e estresse",
       r"\bsas[- ]?2\b", r"sport anxiety scale"),
    _i("STAI", "ansiedade e estresse",
       r"\bstai\b", r"state[- ]trait anxiety inventory"),
    _i("SCAT", "ansiedade e estresse",
       r"\bscat\b", r"sport competition anxiety test"),
    _i("PSS (Perceived Stress Scale)", "ansiedade e estresse",
       r"\bpss[- ]?(?:4|10|14)?\b", r"perceived stress scale"),
    _i("RESTQ-Sport", "ansiedade e estresse",
       r"\brestq\b", r"recovery[- ]stress questionnaire"),
    _i("SAQ / CSAQ", "ansiedade e estresse", r"\bcsaq\b", r"sport anxiety questionnaire"),

    # motivação
    _i("SMS (Sport Motivation Scale)", "motivação",
       r"\bsms[- ]?(?:6|28|ii)?\b(?!.*text)", r"sport motivation scale"),
    _i("TEOSQ", "motivação",
       r"\bteosq\b", r"task and ego orientation"),
    _i("POSQ", "motivação", r"\bposq\b", r"perception of success questionnaire"),
    _i("BRSQ", "motivação", r"\bbrsq\b", r"behaviou?ral regulation in sport"),
    _i("IMI", "motivação", r"\bimi\b", r"intrinsic motivation inventory"),
    _i("PMCSQ", "motivação", r"\bpmcsq(?:-2)?\b", r"perceived motivational climate"),
    _i("BNSSS / PNSE", "motivação", r"\bbnsss\b", r"\bpnse\b",
       r"basic needs? satisfaction"),
    _i("AGQ-S", "motivação", r"\bagq[- ]?s\b", r"achievement goal questionnaire"),

    # cognição e atenção
    _i("Stroop", "cognição e atenção", r"\bstroop\b"),
    _i("Teste d2 de atenção", "cognição e atenção", r"\bd2 test\b", r"\btest d2\b"),
    _i("Trail Making Test", "cognição e atenção", r"trail making"),
    _i("Go/No-Go", "cognição e atenção", r"\bgo[/ ]?no[- ]?go\b"),
    _i("Corsi / span de memória", "cognição e atenção", r"\bcorsi\b", r"\bdigit span\b"),
    _i("Vienna Test System", "cognição e atenção", r"vienna test system"),
    _i("Teste de tomada de decisão em vídeo", "cognição e atenção",
       r"video[- ]based (?:decision|test)", r"decision[- ]making (?:test|task|accuracy)"),
    # "TAIS" sozinho casaria com o português "tais como"; exige-se o nome por extenso.
    _i("TAIS", "cognição e atenção", r"attentional and interpersonal style",
       r"\btais\b(?=[ ,)]*(?:questionnaire|inventory|scale|test))"),

    # burnout e saúde mental
    _i("ABQ (Athlete Burnout Questionnaire)", "burnout e saúde mental",
       r"\babq\b", r"athlete burnout questionnaire"),
    _i("MBI", "burnout e saúde mental", r"\bmbi\b", r"maslach burnout"),
    _i("BDI / BDI-II", "burnout e saúde mental", r"\bbdi(?:-ii)?\b", r"beck depression"),
    _i("PHQ-9", "burnout e saúde mental", r"\bphq[- ]?9\b", r"patient health questionnaire"),
    _i("CES-D", "burnout e saúde mental", r"\bces[- ]?d\b"),
    _i("GHQ-12", "burnout e saúde mental", r"\bghq[- ]?12\b", r"general health questionnaire"),
    _i("DASS-21", "burnout e saúde mental", r"\bdass[- ]?21\b",
       r"depression anxiety stress scale"),
    _i("EAT-26 / imagem corporal", "burnout e saúde mental",
       r"\beat[- ]?26\b", r"eating attitudes test", r"\bedi[- ]?[23]?\b"),

    # coping e resiliência
    _i("ACSI-28", "coping e resiliência", r"\bacsi[- ]?28\b",
       r"athletic coping skills inventory"),
    _i("TOPS", "coping e resiliência", r"\btops\b", r"test of performance strategies"),
    _i("Brief COPE / CSI", "coping e resiliência", r"\bbrief[- ]cope\b",
       r"coping (?:strategies )?inventory"),
    _i("CD-RISC", "coping e resiliência", r"\bcd[- ]?risc\b", r"connor[- ]davidson"),
    _i("MTQ-48", "coping e resiliência", r"\bmtq[- ]?48\b",
       r"mental toughness questionnaire"),
    _i("Escala de resiliência", "coping e resiliência", r"resilience scale"),

    # sono e recuperação
    _i("PSQI", "sono e recuperação", r"\bpsqi\b", r"pittsburgh sleep quality"),
    _i("Epworth (ESS)", "sono e recuperação", r"\bepworth\b", r"\bess\b.{0,20}sleepiness"),
    _i("ASSQ", "sono e recuperação", r"\bassq\b", r"athlete sleep screening"),
    _i("Índice de Hooper", "sono e recuperação", r"hooper (?:index|questionnaire)"),
    _i("TQR", "sono e recuperação", r"\btqr\b", r"total quality recovery"),
    _i("Questionário de bem-estar / wellness", "sono e recuperação",
       r"wellness questionnaire", r"well[- ]being questionnaire",
       r"perceived recovery status"),
    _i("Actigrafia / diário de sono", "sono e recuperação",
       r"\bactigraph", r"sleep diary", r"sleep log"),

    # autoeficácia e confiança
    _i("Escala de autoeficácia geral", "autoeficácia e confiança",
       r"general self[- ]efficacy", r"\bgse\b"),
    _i("SSCI / TSCI", "autoeficácia e confiança", r"\bs?sci\b.{0,20}confidence",
       r"sport confidence inventory"),
    _i("Rosenberg (RSES)", "autoeficácia e confiança", r"rosenberg", r"\brses\b"),
    _i("PSPP", "autoeficácia e confiança", r"\bpspp\b", r"physical self[- ]perception"),

    # humor e afeto
    _i("POMS", "humor e afeto", r"\bpoms\b", r"profile of mood states"),
    _i("BRUMS", "humor e afeto", r"\bbrums\b", r"brunel mood scale"),
    _i("PANAS", "humor e afeto", r"\bpanas\b",
       r"positive and negative affect schedule"),
    _i("Feeling Scale / Felt Arousal", "humor e afeto",
       r"feeling scale", r"felt arousal scale"),
    _i("Escala Visual Analógica de humor", "humor e afeto",
       r"\bvas\b.{0,25}(?:mood|fatigue|humor)"),

    # personalidade
    _i("NEO-FFI / NEO-PI-R", "personalidade", r"\bneo[- ]?(?:ffi|pi[- ]?r)\b"),
    _i("Big Five (BFI / TIPI)", "personalidade", r"\bbfi\b", r"\btipi\b",
       r"big five (?:inventory|personality)"),
    _i("EPQ / EPI (Eysenck)", "personalidade", r"\bepq(?:-r)?\b", r"\beysenck\b"),
    _i("FCB-TI", "personalidade", r"\bfcb[- ]?ti\b",
       r"formal characteristics of behaviou?r"),
    _i("16PF / MMPI", "personalidade", r"\b16pf\b", r"\bmmpi\b"),

    # coesão e grupo
    _i("GEQ (Group Environment Questionnaire)", "coesão e grupo",
       r"\bgeq\b", r"group environment questionnaire"),
    _i("YSEQ", "coesão e grupo", r"\byseq\b", r"youth sport environment"),
    _i("LSS (Leadership Scale for Sports)", "coesão e grupo",
       r"(?<!toxic )leadership scale for sport"),
    _i("CART-Q", "coesão e grupo", r"\bcart[- ]?q\b", r"coach[- ]athlete relationship"),

    # emoção
    _i("TEIQue / SSEIT", "emoção", r"\bteique\b", r"\bsseit\b",
       r"emotional intelligence (?:scale|questionnaire|inventory)"),
    _i("ERQ", "emoção", r"\berq\b", r"emotion regulation questionnaire"),
    _i("SEQ (Sport Emotion Questionnaire)", "emoção", r"\bseq\b",
       r"sport emotion questionnaire"),
)

# Instrumentos psicofísicos: aferem percepção, mas não são psicometria de
# construto. Contam como aferição subjetiva, não como construto psicológico
# isolado — foi a confusão que inflou o corpus em 37% (achado B4).
PSICOFISICOS = (
    ("PSE / Borg", r"\bborg\b", r"\brpe\b", r"rating of perceived exertion",
     r"perceived exertion"),
    ("Escala de dor / desconforto", r"\bvas\b.{0,15}pain", r"pain scale"),
)

_RE = {i.canonico: re.compile("|".join(i.padroes), re.I) for i in INSTRUMENTOS}
_RE_PSICO = {n: re.compile("|".join(p), re.I) for n, *p in
             [(n, *p) for n, *p in PSICOFISICOS]}


def _plano(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return t.lower()


# Rótulos agregados que a biblioteca grava no campo `instrumentos`. Não
# identificam o instrumento efetivamente usado — "SMS/TEOSQ" não diz qual dos
# dois —, então não alimentam o dicionário; são contados à parte.
ROTULOS_GENERICOS = (
    "questionario / escala (generico)",
    "escala de motivacao (sms/teosq)",
    "testes cognitivos / tempo de reacao",
)


def detectar(*campos: str) -> list[Instrumento]:
    """Instrumentos psicométricos nomeados nos campos dados.

    A detecção corre sobre o texto primário (título, resumo, palavras-chave).
    O campo `instrumentos` da biblioteca é derivado e agrega rótulos genéricos,
    de modo que não serve para nomear o instrumento — foi essa confusão que
    produziu a "Tabela 5 de instrumentos psicométricos" cheia de testes físicos.
    """
    texto = _plano(" ".join(c or "" for c in campos))
    for rotulo in ROTULOS_GENERICOS:
        texto = texto.replace(rotulo, " ")
    return [i for i in INSTRUMENTOS if _RE[i.canonico].search(texto)]


def detectar_psicofisicos(*campos: str) -> list[str]:
    texto = _plano(" ".join(c or "" for c in campos))
    return [n for n, rx in _RE_PSICO.items() if rx.search(texto)]


def familias_de(instrumentos: list[Instrumento]) -> set[str]:
    return {i.familia for i in instrumentos}


def resumo_dicionario() -> dict[str, int]:
    d: dict[str, int] = {}
    for i in INSTRUMENTOS:
        d[i.familia] = d.get(i.familia, 0) + 1
    return d
