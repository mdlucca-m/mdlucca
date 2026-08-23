-- médias por atleta com SOMA INTEIRA (escala 1e-4) em vez de avg() em ponto
-- flutuante: a soma paralela do DuckDB reordena e faz o 4º decimal oscilar em
-- valores de fronteira. athlete_day já vem em múltiplos exatos de 1e-4.
with m as (select ID,
                  round(sum(round(vigor*10000)) /(10000.0*count(*)), 4) as vigor_med,
                  round(sum(round(fadiga*10000))/(10000.0*count(*)), 4) as fadiga_med,
                  round(sum(round(pth*10000))   /(10000.0*count(*)), 4) as pth_med,
                  count(*) as n_dias
           from {{ ref('athlete_day') }} group by ID)
select m.*, rsa.BkMel, rsa.BkSoma, rsa.BkF, mdc.clsVigor, mdc.clsFadiga
from m left join {{ ref('rsa') }} rsa on m.ID = rsa.ID
       left join {{ ref('mdc') }} mdc on m.ID = mdc.ID
