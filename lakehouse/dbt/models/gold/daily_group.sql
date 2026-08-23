select dia, any_value(day_type) as day_type,
  round(avg(vigor),4) as vigor, round(avg(fadiga),4) as fadiga, round(avg(tensao),4) as tensao,
  round(avg(depressao),4) as depressao, round(avg(raiva),4) as raiva,
  round(avg(confusao),4) as confusao, round(avg(pth),4) as pth, count(*) as n_atletas
from {{ ref('athlete_day') }} group by dia
