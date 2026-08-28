# Série sobre humor em atletas de handebol: plano, artigos e panorama

Três documentos gerados, todos em ABNT, fundo branco nas figuras, sem
travessão e sem gerúndio no texto.

| documento | arquivo | conteúdo |
|-----------|---------|----------|
| Plano editorial | `data/PLANO_EDITORIAL_HUMOR_HANDEBOL.docx` | decisão, cronograma, delimitação, panorama, lacunas, pendências |
| Artigo 1 | `data/ARTIGO1_PERFIS_HUMOR_HANDEBOL.docx` | perfis de humor: prevalência, psicometria, percentis |
| Artigo 2 | `data/ARTIGO2_FADIGA_PERFIS_HANDEBOL.docx` | impacto da fadiga: assinatura de sobrecarga e recomendações |

## Ordem de publicação e por quê

O Artigo 1 sai primeiro por dependência, não por preferência: o Artigo 2 usa
o perfil como desfecho e precisa citar a definição já publicada. Invertida a
ordem, o Artigo 2 carrega toda a seção de método da classificação e os dois
manuscritos enfraquecem.

## Panorama do corpus

`scripts/panorama/corpus.py` levanta a produção internacional sobre
psicologia do esporte no handebol a partir de `data/BIBLIOTECA_HANDEBOL.sqlite`.
O recorte é handebol mais janela de 2006 a 2026 mais construto psicológico
aferido, sem filtro de delineamento, porque a pergunta inclui as revisões.

| delineamento | estudos | % |
|--------------|---------|---|
| Revisão | 14 | 2,7 |
| Ensaio controlado | 50 | 9,5 |
| Experimental sem controle | 47 | 9,0 |
| Transversal | 41 | 7,8 |
| Longitudinal | 39 | 7,4 |
| Outros | 36 | 6,8 |
| Não especificado no resumo | 298 | 56,8 |
| **Total no escopo** | **525** | **100** |

Humor e afeto aparecem em 32 estudos, 6,1% do escopo, dos quais um é
longitudinal e um é revisão. Nenhum aplica os seis perfis de Parsons-Smith.

## As quatro lacunas

1. Nenhum estudo aplica os seis perfis de humor ao handebol.
2. Falta acompanhamento longitudinal do humor na modalidade.
3. Nenhum estudo liga o deslocamento do perfil ao tipo de carga.
4. O BRUMS quase não é usado em handebol: dois estudos no escopo.

## Os seis perfis e como são calculados

O procedimento de Parsons-Smith, Terry e Machin (2017) padroniza as seis
subescalas em escore T, aplica agrupamento hierárquico aglomerativo com
distância euclidiana quadrática pelo método de Ward, refina por k-médias e
confirma por análise discriminante.

| perfil | padrão | norma (%) | esta amostra (%) |
|--------|--------|-----------|------------------|
| Iceberg | vigor alto, negativas baixas | 29,4 | 13,8 |
| Submerso | as seis abaixo da média | 25,5 | 9,4 |
| Barbatana de tubarão | vigor mais baixo de todos, fadiga alta | 17,3 | 7,2 |
| Superfície | as seis próximas da média | 14,8 | 56,8 |
| Iceberg invertido | vigor baixo, negativas altas | 10,3 | 9,0 |
| Everest invertido | vigor baixo, depressão, raiva e confusão muito altas | 2,7 | 3,7 |

A diferença de 42 pontos percentuais no perfil superfície é efeito da
padronização dentro da amostra, na ausência de normas de escore T para
handebol. O Artigo 1 transforma essa limitação em contribuição ao publicar
percentis próprios da modalidade.

## Variáveis de validação cruzada

Já coletadas: PSE da sessão, FC de pico, recuperação da FC em um minuto,
deriva cardíaca, TQR, sonolência, fadiga física e mental separadas, PSS-14.

Faltam: variabilidade da frequência cardíaca, marcadores bioquímicos com
tabela de resultado e, a mais importante, **medida de desempenho após o
microciclo**. Sem ela, o Artigo 2 descreve assinatura de sobrecarga e não
diagnostica overreaching funcional ou não funcional.

## Pendências bloqueantes

| pendência | prazo |
|-----------|-------|
| Reconciliar 456 observações contra o máximo de 351 do desenho | 06/09 |
| Fixar a estimativa em dois passos como série oficial | 06/09 |
| Escolher o MDC de referência entre alfa, ômega e ICC | 11/10 |
| Publicar percentis próprios no lugar das normas ausentes | 13/09 |
| Registrar o protocolo da revisão | 18/10 |

Falta também a análise bibliométrica sobre qualidade do ar, de Fábio e
Danilo, citada como referência de formato. Ela não está no repositório.

## Como regerar

```
python3 scripts/panorama/corpus.py --json data/panorama.json
python3 scripts/plano/gerar_plano.py
python3 scripts/artigos/gerar.py 1 2
python3 scripts/artigos/verificar.py
python3 scripts/resultados/verificar_estilo.py data/ARTIGO1_PERFIS_HUMOR_HANDEBOL.docx
python3 scripts/resultados/verificar_estilo.py data/ARTIGO2_FADIGA_PERFIS_HANDEBOL.docx
```
