select ID, dia, any_value(day_type) as day_type, any_value(hiit_flag) as hiit_flag,
  round(avg(Vigor),4) as vigor, round(avg(Fadiga),4) as fadiga, round(avg(Tensao),4) as tensao,
  round(avg(Depressao),4) as depressao, round(avg(Raiva),4) as raiva,
  round(avg(Confusao),4) as confusao, round(avg(PTH),4) as pth, count(*) as n_obs
from {{ ref('mood') }} group by ID, dia
