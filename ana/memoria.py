# -*- coding: utf-8 -*-
"""Memória da Ana: o pouco que ela precisa lembrar entre uma sessão e outra.

Não é histórico de conversa. É o que o pesquisador já decidiu e não quer
repetir: a unidade de análise canônica, o periódico-alvo, o padrão de escrita,
o número do CAAE quando ele existir. Cada lembrança tem escopo, data e origem.
"""
from __future__ import annotations
import os, sqlite3, datetime
from pathlib import Path

RAIZ = Path(os.environ.get("ANA_RAIZ") or Path(__file__).resolve().parent)
BANCO = Path(os.environ.get("ANA_MEMORIA") or RAIZ / "memoria.sqlite")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS lembranca(
  chave     TEXT PRIMARY KEY,
  valor     TEXT NOT NULL,
  escopo    TEXT NOT NULL DEFAULT 'geral',
  origem    TEXT,
  criada    TEXT NOT NULL,
  atualizada TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_lembranca_escopo ON lembranca(escopo);
CREATE VIRTUAL TABLE IF NOT EXISTS lembranca_busca
  USING fts5(chave, valor, escopo, content='lembranca', content_rowid='rowid');
"""

def conectar(somente_leitura: bool = False) -> sqlite3.Connection:
    if somente_leitura and BANCO.exists():
        cx = sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True)
    else:
        BANCO.parent.mkdir(parents=True, exist_ok=True)
        cx = sqlite3.connect(BANCO)
        cx.executescript(ESQUEMA)
    cx.row_factory = sqlite3.Row
    return cx

def _agora() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")

def lembrar(chave: str, valor: str, escopo: str = "geral", origem: str | None = None) -> str:
    chave = chave.strip().lower()
    if not chave or not valor.strip():
        return "lembrança vazia: informe chave e valor."
    with conectar() as cx:
        antiga = cx.execute("SELECT valor FROM lembranca WHERE chave=?", (chave,)).fetchone()
        agora = _agora()
        cx.execute(
            "INSERT INTO lembranca(chave,valor,escopo,origem,criada,atualizada)"
            " VALUES(?,?,?,?,?,?)"
            " ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor, escopo=excluded.escopo,"
            " origem=excluded.origem, atualizada=excluded.atualizada",
            (chave, valor.strip(), escopo, origem, agora, agora))
        cx.execute("INSERT INTO lembranca_busca(lembranca_busca) VALUES('rebuild')")
    if antiga and antiga["valor"] != valor.strip():
        return f"lembrança «{chave}» atualizada.\n  antes: {antiga['valor']}\n  agora: {valor.strip()}"
    return f"lembrança «{chave}» guardada no escopo «{escopo}»."

def esquecer(chave: str) -> str:
    with conectar() as cx:
        n = cx.execute("DELETE FROM lembranca WHERE chave=?", (chave.strip().lower(),)).rowcount
        cx.execute("INSERT INTO lembranca_busca(lembranca_busca) VALUES('rebuild')")
    return f"lembrança «{chave}» apagada." if n else f"não havia lembrança «{chave}»."

def recordar(termo: str | None = None, escopo: str | None = None, limite: int = 40) -> list[sqlite3.Row]:
    cx = conectar(somente_leitura=True)
    try:
        if termo:
            try:
                return cx.execute(
                    "SELECT l.* FROM lembranca_busca b JOIN lembranca l ON l.rowid=b.rowid"
                    " WHERE lembranca_busca MATCH ? ORDER BY l.atualizada DESC LIMIT ?",
                    (termo, limite)).fetchall()
            except sqlite3.OperationalError:
                pass  # termo que o FTS não aceita: cai para o LIKE
            alvo = f"%{termo}%"
            return cx.execute(
                "SELECT * FROM lembranca WHERE chave LIKE ? OR valor LIKE ?"
                " ORDER BY atualizada DESC LIMIT ?", (alvo, alvo, limite)).fetchall()
        if escopo:
            return cx.execute("SELECT * FROM lembranca WHERE escopo=? ORDER BY chave LIMIT ?",
                              (escopo, limite)).fetchall()
        return cx.execute("SELECT * FROM lembranca ORDER BY escopo, chave LIMIT ?", (limite,)).fetchall()
    finally:
        cx.close()

def semear() -> int:
    """As decisões já tomadas neste projeto, para a Ana não perguntar de novo."""
    base = [
        ("unidade de análise canônica", "Par atleta-dia (U-AD), n = 166. As outras três, a saber, U-R (456 "
         "registros), U-286 (primeira e última) e U-PAR (143 pareados), existem e devem ser declaradas, nunca "
         "misturadas.", "handebol"),
        ("regra de composição do valor diário", "D1 teve coleta única e vale a primeira resposta de cada "
         "atleta; as 21 respostas tardias são repetição, e não segunda coleta. De D2 a D7 valem o primeiro "
         "registro do dia (pré) e o último (pós). Ao todo, 285 dos 456 registros compõem os valores diários; os "
         "171 excedentes ficam na base sem entrar no cálculo. O pré não exige hora da manhã: 59 dos 139 "
         "atletas-dia só responderam a partir do meio-dia, sem registro anterior naquele dia. Auditado em "
         "analise/V2_proto.py.", "handebol"),
        ("faixa de risco", "Perfis 3, 4 e 5 da solução: barbatana de tubarão, iceberg invertido e everest invertido.",
         "handebol"),
        ("dia fisiológico", "A virada é às 4h: registro antes das 4h pertence ao dia anterior.", "handebol"),
        ("dados sensíveis", "Backup__Banco_de_dados.xlsx e o HIIT_FC_PSE.xlsx não anonimizado têm nomes reais "
         "ligados a humor e lesão. Não acompanham submissão nem repositório aberto. A anonimização A01–A27 "
         "acontece dentro da rotina de importação.", "handebol"),
        ("padrão de escrita", "Português culto brasileiro, padrão ouro da literatura. Sem gerúndio, sem conectivos "
         "de encadeamento vazios, sem hipérbole. Número sempre com vírgula decimal e sinal menos tipográfico.",
         "escrita"),
        ("regra dos números", "Nenhum número entra em texto sem vir de uma consulta à base ou a um JSON de análise. "
         "Memória não é fonte.", "escrita"),
        ("estudo em curso", "Perfis de humor (BRUMS) de atletas de handebol de elite na última semana de "
         "pré-temporada, 21 a 27 de abril de 2024, 27 atletas. Dois artigos: descritivo-analítico e inferencial.",
         "handebol"),
        ("pendências dos artigos", "Falta o número do CAAE, o financiamento e a contribuição dos autores. "
         "Cinco referências seguem sem DOI. A idade diverge entre 21,96 ± 3,81 e 22,2 ± 3,7.", "handebol"),
        ("duas auditorias", "A de procedência (D1–D6) pergunta de onde vem cada número; a de qualidade "
         "(Q1–Q6) pergunta se o número está certo. As duas estão na tabela auditoria da base. Nenhum erro de "
         "pontuação: 4.113 conferências de escore reconstruído por fórmula, zero divergência.", "handebol"),
        ("correção do achado D2", "O número «136 dos 457 registros fora da semana» estava errado e foi "
         "corrigido em 01/09/2026. Os valores verificados na fonte: 55 registros com ano anterior a 2020, 84 "
         "inutilizáveis pelo campo de data autorreferida (68 fora da semana, 16 em branco) e 88 divergentes do "
         "dia obtido pelo carimbo. Passaram a ser computados a cada execução, não escritos à mão.", "handebol"),
        ("domínio de Epworth", "A coluna de origem dizia 0 a 24, mas o formulário aplicou seis das oito "
         "situações da escala: o máximo possível é 18. Corrigido na tabela variavel.", "handebol"),
        ("triagem de discrepantes", "Ordem obrigatória: domínio da escala primeiro, critérios de dispersão "
         "depois. Em subescala com piso (confusão, e em menor grau depressão e raiva) o IQR é zero, a cerca de "
         "Tukey rotula 19,5% da amostra e o z modificado fica indefinido. Nesses casos a triagem é "
         "intraindividual.", "handebol"),
        ("resposta dose-humor", "As horas do próprio dia não têm efeito detectável; as da véspera têm. Cada "
         "hora de treino de ontem soma 0,433 ponto de fadiga e subtrai 0,407 de vigor hoje (p < 0,001). O "
         "humor da manhã é consequência, não previsão.", "handebol"),
        ("o que comprime o microciclo", "Pela programação linear, cada hora do amistoso de D5 custa 0,416 "
         "ponto do pior dia de vigor da semana — mais do que qualquer decisão de treino disponível. Quem "
         "comprime a semana é o calendário de jogos, não o volume. Carga semanal mínima estruturalmente "
         "viável: 19,17 h.", "handebol"),
        ("filtro das séries", "A curva de cada série de sete pontos vem do filtro binomial 1-2-1, núcleo "
         "[¼, ½, ¼] aplicado aos pontos internos, com os extremos conservados no valor observado porque o "
         "deslocamento total é medido entre eles. O ganho é H(ω) = cos²(ω/2), que se anula em Nyquist. Foram "
         "descartadas a média móvel simples, que não se anula ali e inverte parte da banda alta, e a "
         "Savitzky-Golay, instável nas bordas de série tão curta. O piso de ruído é a média dos sete erros "
         "padrão diários; derivadas e limiares saem em unidades desse piso. Nenhum resíduo do filtro chega a "
         "um piso e meio. Ver analise/V2_cruz.py e ana_cruzamento(parte='filtro').", "handebol"),
        ("anatomia dos cruzamentos", "Cruzamento é zero da série da diferença. A abscissa sai por interpolação "
         "linear, e a travessia tem velocidade, aceleração e zona de indecisão, isto é, o intervalo em que a "
         "diferença fica dentro do limiar combinado √(piso²ᴬ+piso²ᴮ). Inversão estabelecida e data determinada "
         "são coisas distintas: vigor×fadiga inverte de modo estabelecido, mas cruza a 0,86 limiar por dia, com "
         "zona de indecisão de 3,52 dias, de D2,59 a D6,11. Vigor×TMD cruza em D6,01, a 2,14 limiar por dia, "
         "zona de 1,42 dia, e é o único cruzamento nítido. Fadiga×TMD não separa nos extremos: divergência. "
         "Consultar ana_cruzamento.", "handebol"),
        ("decomposição da variação", "Quatro decomposições, em analise/V2_decomp.py. (a) Efeitos aleatórios "
         "cruzados, atleta e dia: a parcela entre dias, que é o objeto do estudo, é a menor das três em todas as "
         "sete variáveis, de 0,6% na depressão a 15,6% no vigor. (b) Fidedignidade da série diária: vigor 0,78 e "
         "fadiga 0,62 sustentam leitura de série; TMD 0,48; tensão e confusão 0,33; raiva 0,08; depressão nula, "
         "porque a variância observada, 0,094, é menor que a de erro, 0,227. (c) Deslocamento em choque e "
         "deriva: o movimento do vigor é 90,7% choque, o do TMD 71,0%, o da fadiga 65,9%; o da depressão é "
         "deriva pura. (d) Identidade do filtro, com o termo de covariância explícito. Consultar "
         "ana_decomposicao.", "handebol"),
        ("sinal pelo piso não é fidedignidade", "Não confundir os dois critérios. O piso de ruído compara o "
         "deslocamento entre extremos com o erro de amostragem; a fidedignidade compara a dispersão das sete "
         "médias com esse mesmo erro. Uma variável pode ter deslocamento acima do piso e série de fidedignidade "
         "nula, como a depressão: ela se move pouco por dia, mas na mesma direção o tempo todo.", "handebol"),
        ("correção do resumo e da conclusão do Artigo 1", "Em 02/09/2026 verificou-se que o resumo, o "
         "abstract e a conclusão do Artigo 1 ainda traziam as prevalências do dia basal calculadas pela regra "
         "anterior, além do deslocamento antigo do vigor e da fadiga. Os valores corretos, conferidos na tabela "
         "prevalencia da base: iceberg 44,4% para 19,0%, barbatana de tubarão 3,7% para 23,8%, faixa de risco "
         "14,8% para 52,4%; vigor −4,33 e fadiga +4,28. O corpo do artigo já estava certo; falhou a propagação "
         "para as peças de abertura e fechamento. Lição: ao mudar a base, conferir resumo, abstract e conclusão "
         "à parte, porque eles repetem números sem os recalcular.", "handebol"),
        ("associação em dois planos", "A correlação agregada dos 166 pares mistura o que separa atletas do que "
         "varia dentro do atleta, e os dois planos podem divergir. Cinco dos vinte e um pares só se associam "
         "dentro do atleta. O caso decisivo é a tensão: com o vigor, ρ = 0,207 e p = 0,300 entre atletas, contra "
         "ρ = 0,329 e p < 0,001 dentro do atleta; com a perturbação total, o ρ agregado de 0,200 desaparece no "
         "plano intraindividual (ρ = 0,015; p = 0,846). A tensão funciona neste elenco como ativação, e não como "
         "sofrimento, com a ressalva de que o efeito de piso de 41,6% oferece explicação métrica alternativa. "
         "Calculado em analise/V2_assoc.py.", "handebol"),
        ("o composto que se degrada", "A correlação entre fadiga e perturbação total sobe de 0,671 no basal a "
         "0,858 no sétimo dia, e a variância partilhada de 45,0% a 73,7%. A tendência do coeficiente ao longo dos "
         "sete dias dá ρ = 0,714 com p = 0,071, portanto não conclusiva: relatar direção e extremos, nunca "
         "tendência significativa. Consequência prática: na fase terminal do ciclo, quem acompanha só o escalar "
         "acompanha a fadiga.", "handebol"),
        ("reconferência", "Os números dos três documentos foram recalculados por um segundo caminho de "
         "código, partindo do item do formulário: 65 de 65 conferências coincidem. Não repetir a "
         "reconferência sem motivo; consultar ana_qualidade(parte='reconferencia').", "handebol"),
    ]
    for chave, valor, escopo in base:
        lembrar(chave, valor, escopo=escopo, origem="semeadura inicial")
    return len(base)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "semear":
        print(f"{semear()} lembranças semeadas em {BANCO}")
    else:
        for r in recordar():
            print(f"[{r['escopo']}] {r['chave']}\n    {r['valor']}")
