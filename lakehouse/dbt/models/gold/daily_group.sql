-- média diária do grupo. Para reprodutibilidade bit-a-bit, a média é calculada
-- por SOMA INTEIRA (escala 1e-4) — independente da ordem de agregação do DuckDB —
-- em vez de avg() em ponto flutuante, cuja soma paralela reordena e faz o 4º
-- decimal oscilar em valores de fronteira. athlete_day já vem arredondado a 4 casas
-- (múltiplos exatos de 1e-4), então round(x*10000) é inteiro exato e a soma é estável.
select dia, any_value(day_type) as day_type,
  round(sum(round(vigor*10000))    / (10000.0*count(*)), 4) as vigor,
  round(sum(round(fadiga*10000))   / (10000.0*count(*)), 4) as fadiga,
  round(sum(round(tensao*10000))   / (10000.0*count(*)), 4) as tensao,
  round(sum(round(depressao*10000))/ (10000.0*count(*)), 4) as depressao,
  round(sum(round(raiva*10000))    / (10000.0*count(*)), 4) as raiva,
  round(sum(round(confusao*10000)) / (10000.0*count(*)), 4) as confusao,
  round(sum(round(pth*10000))      / (10000.0*count(*)), 4) as pth,
  count(*) as n_atletas
from {{ ref('athlete_day') }} group by dia
