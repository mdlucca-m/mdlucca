# Dicionário de dados

Base única: `base/humor_handebol.sqlite`. Os CSV em `base/csv/` são exportações fiéis das tabelas e vistas.

| Objeto | Linhas | Colunas | O que é |
|---|---:|---:|---|
| `v_confronto_vias` | 30 | 5 | Vista: a mesma hipótese pelas três vias de análise. |
| `v_painel_dia` | 7 | 10 | Vista: o painel dia a dia. |
| `v_qualidade` | 20 | 9 | — |
| `v_significativos` | 162 | 11 | Vista: apenas os resultados significativos. |
| `aba` | 218 | 7 | Cada aba das planilhas, categorizada. |
| `atleta` | 27 | 7 | Um registro por atleta, com assiduidade. |
| `atleta_dia` | 166 | 22 | A unidade de análise adotada: um valor por atleta e por dia, com escore T, perfil e faixa. |
| `auditoria` | 12 | 6 | Os seis achados da auditoria, com causa, correção e impacto. |
| `celula` | 282776 | 6 | Acervo célula a célula, com nomes de atletas removidos. |
| `dia` | 7 | 10 | Os sete dias do microciclo, com estímulo, carga e janela de coleta observada. |
| `dicionario` | 20 | 5 | — |
| `fonte` | 6 | 6 | As planilhas de origem, com papel e soma de verificação. |
| `formula` | 14 | 4 | — |
| `otimizacao` | 21 | 5 | — |
| `otimizacao_fronteira` | 9 | 5 | — |
| `otimizacao_restricao` | 5 | 5 | — |
| `pre_pos` | 1309 | 8 | Pares manhã/noite em formato longo, com delta. |
| `prevalencia` | 123 | 8 | Prevalências por unidade de análise, por dia e por estímulo. |
| `qualidade_categorica` | 24 | 6 | — |
| `qualidade_cobertura` | 7 | 7 | — |
| `qualidade_faltante` | 60 | 5 | — |
| `qualidade_numerica` | 19 | 31 | — |
| `reconferencia` | 65 | 6 | — |
| `referencia` | 63 | 13 | Referências com DOI e ligação, quando localizados. |
| `registro` | 456 | 19 | Cada formulário respondido, com momento (pré, pós, único) e período do dia. |
| `resultado` | 355 | 20 | Todo resultado estatístico do estudo em formato longo e consultável. |
| `serie_diaria` | 77 | 9 | Série de cada variável com erro-padrão, suavização, derivadas, piso de ruído e choque. |
| `serie_perfil` | 63 | 8 | O mesmo para a prevalência de cada perfil e faixa. |
| `unidade_analise` | 4 | 6 | As quatro unidades que circulavam nos manuscritos e o viés de cada uma. |
| `variavel` | 11 | 8 | Metadados de cada variável: família, amplitude, direção e norma. |

## Colunas por tabela

**`v_confronto_vias`** — `variavel`, `recorte`, `p_nao_param`, `p_param`, `p_misto`

**`v_painel_dia`** — `dia`, `data`, `tipo_estimulo`, `carga_acumulada`, `n_atletas`, `vigor`, `fadiga`, `pth`, `pct_risco`, `pct_iceberg`

**`v_qualidade`** — `variavel`, `tipo`, `dominio`, `n`, `mediana`, `iqr`, `shapiro_p`, `n_tukey_moderado`, `fora_dominio`

**`v_significativos`** — `dominio`, `via`, `variavel`, `recorte`, `teste`, `p`, `p_ajustado`, `efeito`, `rotulo_efeito`, `n`, `artigo`

**`aba`** — `id`, `fonte_id`, `nome`, `linhas`, `colunas`, `categoria`, `tem_dados`

**`atleta`** — `atleta`, `n_registros`, `n_dias`, `n_pre_pos`, `tem_d1`, `tem_d7`, `assiduidade`

**`atleta_dia`** — `atleta`, `dia`, `n_obs`, `tensao`, `depressao`, `raiva`, `vigor`, `fadiga`, `confusao`, `pth`, `fadiga_fisica`, `fadiga_mental`, `epworth`, `pss`, `t_tensao`, `t_depressao`, `t_raiva`, `t_vigor`, `t_fadiga`, `t_confusao`, `perfil`, `faixa`

**`auditoria`** — `id`, `titulo`, `achado`, `correcao`, `impacto`, `gravidade`

**`celula`** — `aba_id`, `linha`, `coluna`, `cabecalho`, `valor_txt`, `valor_num`

**`dia`** — `dia`, `data`, `tipo_estimulo`, `conteudo`, `horas`, `sessoes`, `carga_acumulada`, `n_registros`, `n_atletas`, `janela`

**`dicionario`** — `variavel`, `tipo`, `escala`, `dominio`, `origem`

**`fonte`** — `id`, `arquivo`, `papel`, `sha256`, `n_abas`, `nota`

**`formula`** — `id`, `nome`, `formula`, `nota`

**`otimizacao`** — `cenario`, `dia`, `horas`, `fadiga_prevista`, `vigor_previsto`

**`otimizacao_fronteira`** — `carga`, `viavel`, `vigor_minimo`, `fadiga_maxima`, `horas`

**`otimizacao_restricao`** — `restricao`, `tipo`, `folga`, `preco_sombra`, `ativa`

**`pre_pos`** — `atleta`, `dia`, `hora_pre`, `hora_pos`, `variavel`, `pre`, `pos`, `delta`

**`prevalencia`** — `id`, `unidade`, `recorte_tipo`, `recorte`, `perfil`, `prevalencia`, `n`, `erro_padrao`

**`qualidade_categorica`** — `variavel`, `nivel`, `f`, `pct`, `f_acum`, `pct_acum`

**`qualidade_cobertura`** — `dia`, `atletas_com_registro`, `atletas_esperados`, `registros`, `registros_esperados`, `cobertura_atleta`, `cobertura_registro`

**`qualidade_faltante`** — `bloco`, `item`, `faltantes`, `n`, `completude`

**`qualidade_numerica`** — `variavel`, `tipo`, `n`, `minimo`, `q1`, `mediana`, `q3`, `maximo`, `media`, `desvio`, `erro_padrao`, `cv`, `iqr`, `mad`, `assimetria`, `curtose`, `shapiro_w`, `shapiro_p`, `tukey_inf`, `tukey_sup`, `n_tukey_moderado`, `n_tukey_extremo`, `n_z3`, `n_zmod`, `fora_dominio`, `iqr_nulo`, `mad_nulo`, `k_sturges`, `k_freedman_diaconis`, `h_freedman_diaconis`, `pct_no_piso`

**`reconferencia`** — `bloco`, `item`, `caminho_a`, `caminho_b`, `diferenca`, `confere`

**`referencia`** — `id`, `autores`, `ano`, `titulo`, `veiculo`, `doi`, `url_doi`, `pubmed`, `url_pubmed`, `open_access`, `url_oa`, `abnt`, `usada_em`

**`registro`** — `id`, `atleta`, `dia`, `carimbo`, `hora`, `periodo`, `momento`, `ordem_no_dia`, `tensao`, `depressao`, `raiva`, `vigor`, `fadiga`, `confusao`, `pth`, `fadiga_fisica`, `fadiga_mental`, `epworth`, `pss`

**`resultado`** — `id`, `dominio`, `via`, `unidade`, `variavel`, `recorte`, `teste`, `estatistica`, `rotulo_estatistica`, `gl`, `p`, `p_ajustado`, `metodo_ajuste`, `efeito`, `rotulo_efeito`, `ic_inf`, `ic_sup`, `n`, `significativo`, `artigo`

**`serie_diaria`** — `variavel`, `dia`, `media`, `erro_padrao`, `suavizado`, `derivada1`, `derivada2`, `piso_ruido`, `e_choque`

**`serie_perfil`** — `perfil`, `dia`, `prevalencia`, `erro_padrao`, `suavizado`, `derivada1`, `piso_ruido`, `e_choque`

**`unidade_analise`** — `sigla`, `nome`, `n`, `regra`, `usada_em`, `vies`

**`variavel`** — `variavel`, `rotulo`, `familia`, `minimo`, `maximo`, `direcao`, `norma_m`, `norma_dp`
