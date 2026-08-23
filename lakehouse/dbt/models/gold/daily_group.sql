select dia, any_value(day_type) as day_type,
  avg(vigor) as vigor, avg(fadiga) as fadiga, avg(tensao) as tensao, avg(depressao) as depressao,
  avg(raiva) as raiva, avg(confusao) as confusao, avg(pth) as pth, count(*) as n_atletas
from {{ ref('athlete_day') }} group by dia
