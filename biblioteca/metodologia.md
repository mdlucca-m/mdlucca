# Metodologia — Esportes Estéticos Femininos

**Escopo:** ginástica rítmica/artística/acrobática, patinação artística, nado artístico/sincronizado, balé/dança, cheerleading.
**Data:** 2026-08-12 · **Fonte de busca nesta sessão:** PubMed/MEDLINE (E-utilities).
**Aviso de disponibilidade:** as buscas via Scite e Consensus não puderam ser executadas nesta sessão (limite mensal de chamadas atingido). As buscas e a verificação foram feitas no PubMed; recomenda-se replicar em Scopus/Web of Science/SPORTDiscus na revisão definitiva.

---

## DELIVERABLE A — Quantos estudos de PERMANOVA foram feitos?

### Resposta direta

**Zero.** Não foi encontrado nenhum estudo que aplique **PERMANOVA (Permutational Multivariate Analysis of Variance)** em **esportes estéticos femininos**.

- `PERMANOVA AND (gymnastics OR "figure skating" OR "artistic swimming" OR ballet OR dance OR cheerleading)` → **0 resultados** no PubMed.
- `PERMANOVA AND "rhythmic gymnastics"` → **0 resultados**.
- `PERMANOVA AND (gymnast OR dancer OR skater OR swimmer)` → 1 resultado, que é um estudo de **ecologia de besouros aquáticos**, não de atletas.
- `PERMANOVA AND ("motor unit" OR "firing rate" OR EMG OR kinematics)` → 1 resultado, que é um estudo de **localização femoral em cirurgia de LPFM (4D-CT)**, não de esporte estético.

### Contexto: onde a PERMANOVA aparece de fato

Ampliando a busca para todo o esporte/exercício (`PERMANOVA AND (sport OR exercise OR movement OR gait)`), o PubMed retorna **~56 registros**. A leitura dos resumos mostra que a esmagadora maioria é de:

- **Microbioma intestinal** — beta-diversidade (distâncias Bray-Curtis / UniFrac / Jaccard) associada a atividade física. Ex.: microbiota e padrões de atividade em idosos ([DOI](https://doi.org/10.19723/j.issn.1671-167X.2026.03.015)); microbiota materna na gravidez ([DOI](https://doi.org/10.3389/fcimb.2026.1747305)); exercício regular e microbiota em chineses de meia-idade ([DOI](https://doi.org/10.1123/ijsnem.2021-0065)).
- **Ecologia** — ex.: óleos essenciais em macieiras ([DOI](https://doi.org/10.3389/fpls.2021.650132)); assembleias de besouros aquáticos ([DOI](https://doi.org/10.3897/BDJ.14.e192023)).

Os **únicos** registros que aplicam PERMANOVA a dados multivariados **humanos de movimento/desempenho** — e **nenhum é esporte estético** — são:

| Estudo | Uso da PERMANOVA | Por que não conta |
|---|---|---|
| Roete et al., 2026 — talento em ciclismo ([DOI](https://doi.org/10.23736/S0022-4707.26.17374-5)) | Diferenças por sexo em características antropométricas/fisiológicas/psicológicas | Ciclismo; amostra mista (27 H / 10 M) |
| Jeong et al., 2024 — marcha na hipermobilidade pediátrica ([DOI](https://doi.org/10.1016/j.jbiomech.2024.112151)) | PERMANOVA + statistical non-parametric mapping para acoplamento inter-articular | População clínica pediátrica, não esporte estético |
| Domaradzki & Słowińska-Lisowska, 2025 — AF-dieta e distress ([DOI](https://doi.org/10.3390/nu17142307)) | Diferenças na coestrutura AF-dieta | Universitários; não esporte estético |
| Wei et al., 2026 — LPFM 4D-CT ([DOI](https://doi.org/10.3390/diagnostics16040508)) | pseudo-F para distribuição espacial de ponto femoral | Cirurgia ortopédica; não esporte estético |

### Cruzamento com a biblioteca de 59 DOIs

Nenhum dos 59 DOIs usa PERMANOVA. O **candidato mais provável** — o estudo de **sinergias musculares do salto Axel na patinação artística** ([DOI](https://doi.org/10.3389/fbioe.2025.1639807)) — usa **Non-negative Matrix Factorization (NMF)** para as sinergias e testes **F/ANOVA** para pesos musculares, **não** PERMANOVA. Os demais artigos de EMG/cinemática/sinergia da biblioteca seguem o mesmo padrão do campo (SPM, NMF/NNMF, ANOVA).

### Conclusão honesta

PERMANOVA é um método típico de **ecologia e microbioma** (dados de composição, matrizes de distância, alta dimensionalidade). Em **biomecânica de esportes estéticos femininos** ele é **essencialmente ausente** na literatura indexada. Uma revisão sistemática com a pergunta "PERMANOVA em esportes estéticos" terá como achado central uma **lacuna (n = 0)** — resultado legítimo e reportável, que deve ser enquadrado como *evidence gap map*.

### Métodos estatísticos que DE FATO dominam o campo

1. **SPM / SPM1d** (e statistical non-parametric mapping) — comparação de curvas cinemáticas e de EMG ao longo do ciclo do movimento. Ex.: laterality em pirouette de balé ([DOI](https://doi.org/10.21091/mppa.2024.1002)); aterrissagens em cheerleaders ([DOI](https://doi.org/10.3389/fspor.2024.1419783)).
2. **NMF / NNMF de sinergias musculares**, muitas vezes com **K-means** e **correlação de Pearson**. Ex.: salto Axel ([DOI](https://doi.org/10.3389/fbioe.2025.1639807)); aterrissagem em dançarinas de Latin ([DOI](https://doi.org/10.3390/biomimetics9080489)); support scale na ginástica ([DOI](https://doi.org/10.1519/JSC.0000000000005074)).
3. **ANOVA de medidas repetidas / fatorial** com tamanho de efeito (η²) e post-hoc.
4. **Modelos mistos lineares** para dados longitudinais de carga/bem-estar.
5. **PCA** para redução dimensional; **correlação/regressão** para determinantes.
6. **SEM / mediação-moderação** para desfechos psicológicos (perfeccionismo, ansiedade, imagem corporal).

---

## DELIVERABLE B — Mapa de desenhos e métodos para uma revisão sistemática de alta qualidade

### Desenhos de estudo dominantes (estimativa a partir da biblioteca de 59 + literatura recuperada)

| Desenho | Participação aprox. | Observações |
|---|---|---|
| **Transversal** (survey e laboratório de corte único) | ~55–65% | Psicometria e caracterização antropométrica/fisiológica/biomecânica. RoB: **AXIS**. |
| **Experimental / quase-experimental de laboratório** | ~15–20% | EMG+cinemática, intervenções agudas (cafeína, bicarbonato), treino de core; amostras pequenas (n = 7–22), maioria intra-sujeitos. |
| **Longitudinal / coorte** | ~12–15% | Monitoramento de carga/bem-estar, temporada, densidade óssea, follow-up de lesões (até 11 anos). RoB: **Newcastle-Ottawa / ROBINS-I**. |
| **Revisão sistemática/narrativa** | ~5–8% | Ex.: revisões de lesões em cheerleading. Qualidade: **AMSTAR-2 / ROBIS**. |
| **ECR** | <5% | Muito raro; intervenções psicológicas ou de treino. RoB: **RoB2**. |
| **Estudo de caso / série** | ~3–5% | Ex.: coativação na ginástica rítmica (two-case). Valor exploratório. |

### Métodos estatísticos dominantes
Ver lista do Deliverable A (SPM1d, NMF/NNMF, ANOVA de medidas repetidas, modelos mistos, PCA, correlação/regressão, SEM/mediação). **Métodos multivariados por permutação (PERMANOVA) são raros/ausentes** — oportunidade metodológica.

### Lacunas-chave (e desenhos que as preencheriam)

- **Comportamento de unidades motoras** (firing rate, recrutamento, EMG de alta densidade decomposto) em atletas **femininas** de esportes estéticos — hoje só há *proxies* em populações não-estéticas/mistas. → Estudos transversais de laboratório com HD-sEMG e comparação por nível/idade.
- **Estatística multivariada robusta** (PERMANOVA, ML) sobre dados de EMG/cinemática. → Reanálises e estudos metodológicos.
- **Flow** e estados ótimos de desempenho. → Estudos longitudinais/ecológicos (EMA).
- **Burnout, assédio/abuso, saúde mental de longo prazo**. → Coortes prospectivas (hoje quase tudo é transversal).
- **RED-S, função menstrual, saúde óssea**. → Coortes prospectivas com mediadores mecânicos.
- **Prevenção de lesões de aterrissagem e de distúrbios alimentares**. → **ECR**.
- **Padronização de sinergias musculares** (nº de sinergias, critério VAF, normalização) para viabilizar meta-análise.
- **Amostras pequenas / ausência de cálculo de poder**; poucos estudos multicêntricos de elite feminina.

### Scaffold PRISMA

- **Bases:** PubMed/MEDLINE, Scopus, Web of Science, SPORTDiscus, Embase, Cochrane CENTRAL, PsycINFO + literatura cinzenta (ClinicalTrials.gov, ProQuest, busca manual de referências).
- **PICOS:**
  - **P** — atletas do sexo feminino de esportes estéticos, qualquer nível; subgrupos por idade/maturação.
  - **I** — método/exposição de interesse (ex.: análise por PERMANOVA ou, amplo, método estatístico multivariado sobre EMG/cinemática/sinergias) ou intervenção de treino/psicológica.
  - **C** — nível de habilidade, controle não-atleta, membro dominante vs não-dominante, pré vs pós, ou método estatístico alternativo (ANOVA/SPM/NMF).
  - **O** — biomecânicos/neuromusculares, desempenho, carga/bem-estar, psicológicos, saúde (RED-S, lesões).
  - **S** — transversal, longitudinal/coorte, quase-experimental, ECR, estudo de caso; peer-reviewed internacional; idiomas definidos a priori.
- **Risco de viés por desenho:** ECR → **RoB2**; Coorte/Longitudinal → **Newcastle-Ottawa / ROBINS-I**; Transversal → **AXIS**; Revisão → **AMSTAR-2 / ROBIS**.
- **Síntese:** predominantemente **narrativa estruturada** (tabelas por desenho/esporte/método/desfecho), dada a heterogeneidade. Meta-análise só em subgrupos homogêneos (ex.: forças de reação de aterrissagem, prevalência de distúrbios alimentares) com efeitos aleatórios e I²; viés de publicação (funnel/Egger) se ≥10 estudos. Para a pergunta PERMANOVA, **mapa de lacuna de evidência**. Certeza global por **GRADE**. Relato conforme **PRISMA 2020**; protocolo registrado no **PROSPERO**.

---

## Referências (recuperadas via PubMed nesta sessão)

Atribuição: dados bibliográficos obtidos do **PubMed**.

- Roete AJ, et al. (2026). From talented junior to World Tour cyclist. *J Sports Med Phys Fitness*. https://doi.org/10.23736/S0022-4707.26.17374-5
- Jeong H-J, et al. (2024). Lower extremity inter-joint coupling angles and variability during gait in pediatric hypermobility spectrum disorder. *J Biomech*. https://doi.org/10.1016/j.jbiomech.2024.112151
- Domaradzki J, Słowińska-Lisowska MR (2025). Co-Structure of Physical Activity and Dietary Patterns in Relation to Emotional Well-Being. *Nutrients*. https://doi.org/10.3390/nu17142307
- Wei J, et al. (2026). Motion-Informed, Patient-Specific Femoral Localization for MPFL Reconstruction Using 4D-CT. *Diagnostics*. https://doi.org/10.3390/diagnostics16040508
- Yu J, Li M, Chen Z (2025). Bilateral lower extremity joint mechanics and muscle synergy patterns in Axel jumps (elite vs amateur skaters). *Front Bioeng Biotechnol*. https://doi.org/10.3389/fbioe.2025.1639807
- Rosaci G, et al. (2025). Electromyographic Analysis of the Support Scale in Gymnastics. *J Strength Cond Res*. https://doi.org/10.1519/JSC.0000000000005074
- Gao X, et al. (2024). Adaptive Adjustments in Lower Limb Muscle Coordination during Single-Leg Landing in Latin Dancers. *Biomimetics*. https://doi.org/10.3390/biomimetics9080489
- Müller A, Rockenfeller R, Aiyangar AK (2024). Individual factors determine landing impacts in rested and fatigued cheerleaders. *Front Sports Act Living*. https://doi.org/10.3389/fspor.2024.1419783
- Tsubaki Y, et al. (2024). Laterality in Body Coordination of Professional and Amateur Ballet Dancers during a Single Pirouette with Pointe Shoes. *Med Probl Perform Art*. https://doi.org/10.21091/mppa.2024.1002
- Shi J, et al. (2022). Association Between Long-Term Regular Exercise and Gut Microbiota. *Int J Sport Nutr Exerc Metab*. https://doi.org/10.1123/ijsnem.2021-0065
- Guellaf A, Bennas N, Kettani K (2026). Aquatic beetle assemblages in the Martil River. *Biodivers Data J*. https://doi.org/10.3897/BDJ.14.e192023

*Contexto adicional de microbioma/PERMANOVA (não esporte estético): https://doi.org/10.19723/j.issn.1671-167X.2026.03.015 · https://doi.org/10.3389/fcimb.2026.1747305 · https://doi.org/10.3389/fpls.2021.650132*
