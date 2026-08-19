# Auditoria dos dados e documentos — Handebol 2024 (BRUMS × T-CAR × HIIT)

## 1. Inventário dos documentos e dados

| Fonte | O que é | Amostra | Conteúdo |
|---|---|---|---|
| `Handebol_2024.xlsx` (mestre) | Ensaio controlado PVT-CAR/HIIT | 12 Exp + 12 Ctrl = **24** | T-car PV pré/pós, CMJ, Baker/RSA, carga interna (%FC, TRIMP, PSE, sPSE); análises já feitas (equivalência, ANOVA mista, ANCOVA, respondedores) |
| `tese.docx` | Tese de doutorado | 24 (12+12) | **Só fisiológico** (PVT-CAR, TIAI, carga, testes físicos). **Zero BRUMS/humor** |
| `Artigo_Unificado...docx` | Artigo de perfil do humor | 27 | **Já integra** BRUMS + T-CAR + HIIT + sono/estresse + derivadas + alometria + ROC + sinal/ruído (28 figuras, 21 tabelas) |
| `artigo_perfil...docx` | Rascunho antigo do artigo de humor | 27 | Só BRUMS (versão pré-expansão) |
| `Paper1_Humor_completo` (meu) | Versão completa que montei | 27 | BRUMS + derivadas + polinômio + cruzamentos + agudo/recuperação (sem T-car/HIIT) |

**Conclusão do inventário:** a tese e o artigo de humor são **dois estudos distintos**. O estudo de humor (foco deste trabalho) é **grupo único observacional, sem grupo controle** (27 atletas monitorados em condições ecológicas). O rótulo "Experimental/Controle" existente no `Handebol_2024.xlsx` pertence ao estudo fisiológico da tese e **não se aplica ao estudo de humor**. O `Artigo_Unificado` já é a integração fisiológico-psicológica mais avançada que existe.

> Nota: o T-car e a carga entram no estudo de humor como **covariáveis de linha de base e fatores dentro da semana** (aptidão, dias com/sem HIIT), não como comparação entre grupos.

## 2. Reconciliação de dados (crítico)

- `phys.csv`/`tcar_features` (derivados, 27 atletas) **divergem** do mestre autoritativo (24): 9 valores de PV diferentes (ex.: A01 15,1 vs 15,5; A06 15,6 vs 16,4) e 3 atletas sem correspondência no mestre.
- O `%FCmáx` do HIIT do microciclo que calculei do xlsx bruto (~96%) estava **inflado** (usei pico/pico). O valor correto do mestre para a intervenção é **%FCmáx ≈ 78%**; para as séries, ≈ 90%.
- **Recomendação:** usar o mestre `Handebol_2024.xlsx` como fonte autoritativa de T-car e carga; manter o BRUMS do microciclo (27) para o humor, e ligar por nome (24 atletas casam).

## 3. Resultado que MELHORA com os dados autoritativos

T-car pré (PV) × humor semanal, Spearman, **n = 24 (dados do mestre)**:

| Relação | ρ | p |
|---|---|---|
| PV × **Vigor** | **+0,49** | **0,015** |
| PV × **Fadiga física** | **−0,51** | **0,011** |
| PV × PTH | −0,38 | 0,067 |
| PV × Fadiga | −0,35 | 0,093 |
| PV × Depressão | −0,15 | 0,481 (piso) |

Tercis de aptidão (PV 13,9 / 14,6 / 16,2 km/h) × humor semanal:
- **Vigor**: 4,6 / 4,4 / 7,5 (Kruskal p = 0,034)
- **Depressão**: 2,2 / 0,2 / 0,6 (p = 0,014)
- Fadiga física: 6,9 / 5,5 / 5,2 (p = 0,052)

**Interpretação:** atletas mais aptos (maior pico de velocidade no T-car) chegam e permanecem com mais vigor e menos fadiga física ao longo da semana. Com os dados corretos, as relações ficam **mais fortes e significativas** do que no rascunho (que trazia p limítrofes).

## 4. Dias com HIIT (2, 4, 7) vs sem HIIT (1, 3, 5, 6) — humor por atleta

| Dimensão | HIIT | sem HIIT | dz | p |
|---|---|---|---|---|
| Vigor | 4,99 | 6,12 | **−1,36** | <0,001 |
| PTH | 5,98 | 2,98 | **+0,77** | <0,001 |
| Fadiga | 5,87 | 4,88 | **+0,68** | 0,003 |
| Fadiga física | 6,24 | 5,33 | +0,63 | 0,010 |
| Depressão | 1,37 | 0,92 | +0,33 | 0,112 (piso) |

**A deterioração do humor é conduzida pelos dias de HIIT.** A depressão sobe, mas sem significância pelo efeito de piso (67–79% de zeros).

## 5. Inconsistências a corrigir no `Artigo_Unificado` (auditadas)

1. **"Fadiga física/mental" sem instrumento nos Métodos** — usada em resultados centrais (existe como `FadFisica`/`FadMental` nos dados; precisa ser descrita).
2. **Tabela 18 (sinal/ruído) contradiz o texto** — texto cita AUC 0,85/0,90 da fadiga física; a tabela não tem essa linha (máx 0,78).
3. **Contagem de iceberg no D1 diverge** (9 / 13 / 17 em fontes diferentes).
4. **"Barbatana o mais frequente no D7"** — empata com superfície (28,3% cada).
5. **456 observações** incompatível com 27 × 2 × 7 = **378**.
6. **ρ aptidão×fadiga física** aparece como −0,54 e −0,49 em pontos diferentes.
7. **H1 parcialmente contrariada** — tensão (d=−0,59) e confusão mudaram significativamente, não ficaram "estáveis por piso".
8. **Carga interna do microciclo não quantificada** — HIIT entrava como binário; agora temos FC/PSE por sessão (xlsx) para dar dose.
9. **Limiar de PV 14,9 = média amostral** (AUC 0,69, n pequeno) — robustez limitada.
10. Escores T auto-referenciados (T>100 são artefato de piso). Travessões e gerúndios pervasivos.

## 6. Inconsistências na tese (auditadas)

- **Desenho ambíguo:** ora "grupos paralelos randomizados (12×12)", ora "dois semestres com a mesma equipe" (as próprias limitações admitem os semestres). Ponto mais sério.
- **Índice de fadiga (Baker IF) melhorou MAIS no controle** (−31%, p=0,010) que no experimental (−16%, n.s.) — contraintuitivo, não problematizado.
- Baker (soma e melhor tempo) melhora em ambos os grupos (sem interação) — a única variável com efeito exclusivo do TIAI é o **PVT-CAR** (+9,7%, d=1,31; interação d=2,63), com possível circularidade (o treino imita o teste).
- Rótulo "Baker IF (s)" (é %); "14, 88" com espaço; texto duplicado/corrompido em vários pontos; referências incompletas e com duplicatas; verbos no futuro (resíduo de projeto).

## 7. Recomendações

1. Adotar `Handebol_2024.xlsx` como fonte autoritativa de fisiologia; refazer os números de T-car/carga do artigo de humor com ele (ficam mais fortes).
2. Descrever a fadiga física/mental nos Métodos ou removê-la das análises centrais.
3. Corrigir as 10 inconsistências do artigo unificado e as da tese.
4. Quantificar a carga interna do microciclo (FC/PSE por sessão, do xlsx) em vez do HIIT binário.
5. Padronizar (sem travessões, sem gerúndios, sem espaçamento entre parágrafos, fundo branco/sem grade nas figuras).
