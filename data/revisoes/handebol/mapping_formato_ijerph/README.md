# Revisão de mapeamento no formato dos artigos modelo do grupo

Versão de 29/10/2026 do MAPPING REVIEW (variáveis psicológicas no treinamento e na competição do handebol, 199 estudos),
com a linguagem e a metodologia dos artigos modelo do Lape: Andrade et al. (2023), *IJERPH* 20, 3506, e Truppel et al.
(2025), *Atmosphere* 16, 1229.

- Estrutura: 1. Introdução (termina no objetivo); 2. Métodos (2.1 Diretrizes, 2.2 Estratégia de Busca, 2.3 Critérios de
  Elegibilidade, 2.4 Extração e Análise dos Dados, com as QP1 a QP5 no fim); 3. Resultados (respostas às QP, como nos
  modelos); 4. Discussão (4.1 a 4.4 por tópicos, 4.5 Limitações e Estudos Futuros, 4.6 Inovações, Pontos Fortes e
  Aplicações Práticas); 5. Conclusões, em tópicos.
- Análise descritiva, como nos modelos; saíram do texto a triangulação temporal e a razão sinal/ruído.
- 15 figuras (em 4K, sete em 3D: barras, esferas e pizzas) e 7 tabelas; introdução com 80 referências citadas.
  das intervenções (Figura 11), indicadores das intervenções (Figura 12) e domínio × direção do achado (Figura 13).
- Citações autor-data no texto (APA) e referências em ordem alfabética.

Gerador: `corrigidos/modelo_mdpi/gerar_ijerph.py` (figuras novas em `figs_ijerph.py`).

## Outras versões
- `mapping_review_abnt.docx` / `.pdf`: versão ABNT (66 páginas), com o mesmo texto simplificado.
- `mapping_review_documento.docx` / `.pdf`: mesmo conteúdo da versão em artigo, em documento simples (Times 12, espaço 1,5, margens de 3 e 2 cm), sem diagramação de artigo (84 páginas).

## Revisão de 04/11/2026
- Resultados da QP1 na mesma ordem e com as mesmas expressões do artigo modelo: estudo mais antigo e anos, populações,
  países, delineamentos e participantes.
- Discussão ampliada com coortes, monitoramento, intervenções e revisões recentes do handebol (2024 a 2026).
- Conclusão reescrita: "Conclui-se que...", cinco tópicos, um parágrafo de reflexão e um parágrafo de aplicação.

## Estudos de intervenção (documentos separados)
- `tabela_estudos_intervencao_mapping.docx` / `.pdf`: tabela em paisagem com os 24 estudos de intervenção (tipo e
  descrição, duração, população e amostra, modelo do estudo, momentos de medida, desfechos e instrumentos, resultados e
  direção), organizados por tipo de intervenção e ano.
- `texto_resultados_intervencao_mapping.docx` / `.pdf`: texto com os resultados de cada estudo de intervenção, por tipo,
  com síntese por tipo e síntese geral.
- Resultados retirados da extração com citação literal conferida (`DESFECHOS_199.xlsx`); amostra e delineamento
  corrigidos pela leitura integral quando diferem da planilha. Gerador: `gerar_intervencoes_mapping.py` (dados em
  `intervencoes_detalhe.py`).
