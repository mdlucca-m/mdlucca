select ID, dia, any_value(day_type) as day_type, any_value(hiit_flag) as hiit_flag,
  avg(Vigor) as vigor, avg(Fadiga) as fadiga, avg(Tensao) as tensao, avg(Depressao) as depressao,
  avg(Raiva) as raiva, avg(Confusao) as confusao, avg(PTH) as pth, count(*) as n_obs
from {{ ref('mood') }} group by ID, dia
