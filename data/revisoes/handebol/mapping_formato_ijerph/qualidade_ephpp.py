# Qualidade metodológica dos estudos de intervenção pelo EPHPP (Thomas et al., 2004).
# Componentes: sel (viés de seleção), del (delineamento), conf (fatores de confusão), ceg (cegamento),
# col (métodos de coleta de dados), perd (perdas e desistências). F: forte; M: moderado; Fr: fraco.
# Regras do dicionário do instrumento: componente não descrito = fraco (seleção, confusão, coleta e perdas) e
# moderado (cegamento); sem grupo de comparação = confusão fraca; estudo cruzado = confusão forte.
# Fonte das informações: leitura integral de 11/11/2026 (texto completo de acesso aberto; resumo em 16, 173 e 199).

Q = {
    2: dict(sel="M", del_="M", conf="Fr", ceg="Fr", col="M", perd="Fr",
            j="equipe única; linha de base × tratamento sem controle; jogadores informados e avaliação pelo próprio psicólogo; observação por categorias publicadas, sem concordância; perdas não relatadas"),
    16: dict(sel="Fr", del_="F", conf="Fr", ceg="M", col="M", perd="Fr",
             j="só resumo: recrutamento, linha de base e perdas não descritos; grupo controle; CSAI-2 e CBQ validados"),
    50: dict(sel="M", del_="F", conf="Fr", ceg="M", col="F", perd="Fr",
             j="seleção aleatória de jogadoras da liga; dois grupos; linha de base não comparada; escalas persas com confiabilidade relatada; perdas não relatadas"),
    57: dict(sel="M", del_="F", conf="F", ceg="M", col="M", perd="F",
             j="equipe de elite; ensaio randomizado duplo-cego; sem diferenças na linha de base; participantes informados do objetivo; POMS adaptado sem confiabilidade na amostra; 25 analisados"),
    61: dict(sel="M", del_="F", conf="F", ceg="M", col="F", perd="M",
             j="voluntárias; ensaio randomizado estratificado; sem diferenças na linha de base; cegamento não descrito; alfa na amostra; 70% concluíram"),
    81: dict(sel="Fr", del_="F", conf="Fr", ceg="M", col="Fr", perd="Fr",
             j="58% da população de estudantes; dois grupos com pré e pós-teste; grupos não comparados na linha de base; testes técnicos sem validade; perdas não relatadas"),
    89: dict(sel="M", del_="F", conf="F", ceg="M", col="M", perd="Fr",
             j="voluntárias; cruzado randomizado; escalas de Hooper e de Borg sem confiabilidade na amostra; perdas não relatadas"),
    94: dict(sel="M", del_="F", conf="Fr", ceg="M", col="F", perd="F",
             j="jogadoras das seleções chilenas; três grupos randomizados; linha de base não comparada; participantes sem conhecer a hipótese, pesquisador ciente do grupo; alfa na amostra; 13 por grupo até o fim"),
    107: dict(sel="Fr", del_="F", conf="F", ceg="M", col="M", perd="F",
              j="11 de 40 jogadores (27,5%); cruzado com ordem aleatória; sono prévio semelhante; cegamento não descrito; PSQI e KSS sem confiabilidade na amostra; uma condição excluída"),
    111: None,
    119: dict(sel="M", del_="F", conf="Fr", ceg="M", col="F", perd="F",
              j="jogadoras de elite, 70 de 73 concluíram; três grupos randomizados; linha de base não comparada; participantes sem conhecer a hipótese; alfa na amostra"),
    127: dict(sel="M", del_="F", conf="Fr", ceg="M", col="M", perd="Fr",
              j="equipes inteiras por conveniência; controlado não randomizado; diferenças na linha de base sem ajuste; escala validada sem confiabilidade na amostra; perdas não relatadas"),
    128: dict(sel="M", del_="Fr", conf="Fr", ceg="M", col="F", perd="Fr",
              j="seleção intencional; apenas pós-teste e sem grupo controle; escalas validadas com alfa; perdas não relatadas"),
    132: dict(sel="M", del_="F", conf="F", ceg="F", col="M", perd="M",
              j="voluntárias; cruzado randomizado duplo-cego com placebo; hipótese não informada; PSQI árabe validado sem confiabilidade na amostra; 13 de 20 concluíram (65%)"),
    145: dict(sel="M", del_="F", conf="Fr", ceg="M", col="Fr", perd="Fr",
              j="seleção intencional; randomizado; controle com escores maiores no pré-teste sem ajuste; teste próprio sem validade; perdas não relatadas"),
    153: dict(sel="M", del_="F", conf="Fr", ceg="M", col="F", perd="F",
              j="voluntários; controlado não randomizado; diferenças em três dimensões do fluxo e no volume de treino sem ajuste; versões brasileiras com alfa; 105 de 120 analisados"),
    170: dict(sel="M", del_="F", conf="Fr", ceg="M", col="M", perd="F",
              j="equipe principal de um clube; randomizado; desequilíbrio da ansiedade inicial sem ajuste; STAI e SAS-2 validados, confiabilidade só dos autores originais; 8 de 10 na ansiedade pré-competitiva"),
    171: dict(sel="M", del_="F", conf="F", ceg="M", col="F", perd="Fr",
              j="conveniência; controlado não randomizado; sem diferenças na linha de base e idade como covariável; alfa e ômega na amostra; perdas e n por grupo não relatados"),
    173: dict(sel="Fr", del_="F", conf="Fr", ceg="M", col="Fr", perd="Fr",
              j="só resumo: ensaio randomizado de três braços; recrutamento, linha de base, instrumentos e perdas não descritos"),
    174: dict(sel="M", del_="F", conf="Fr", ceg="Fr", col="M", perd="F",
              j="voluntários de uma equipe; ensaio randomizado; linha de base não testada; sem cegamento nem placebo; escala de recuperação sem confiabilidade; sem perdas"),
    179: dict(sel="M", del_="F", conf="F", ceg="M", col="M", perd="F",
              j="estudantes de um instituto; ensaio randomizado de quatro grupos; diferenças iniciais ajustadas pelo pré-teste; bateria padronizada sem confiabilidade na amostra; 10 por grupo analisados"),
    192: dict(sel="M", del_="F", conf="F", ceg="M", col="M", perd="F",
              j="convidados, todos aceitaram; cruzado randomizado; escala visual de diversão sem confiabilidade; 22 concluíram"),
    196: dict(sel="M", del_="F", conf="Fr", ceg="M", col="M", perd="F",
              j="todas as elegíveis de dois clubes; controlado por clube; diferenças na linha de base pelos números da tabela, sem ajuste; avaliadores não cegos; alfa calculado e não informado; todas concluíram"),
    199: dict(sel="Fr", del_="F", conf="Fr", ceg="M", col="M", perd="Fr",
              j="só resumo: ensaio randomizado com controle ativo; recrutamento, linha de base e perdas não descritos; tarefas cognitivas padronizadas"),
}
ROT = {"F": "Forte", "M": "Moderado", "Fr": "Fraco"}


def global_(q):
    fr = sum(v == "Fr" for k, v in q.items() if k != "j")
    return "Forte" if fr == 0 else ("Moderada" if fr == 1 else "Fraca")
