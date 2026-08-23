with m as (select ID, round(avg(vigor),4) as vigor_med, round(avg(fadiga),4) as fadiga_med,
                  round(avg(pth),4) as pth_med, count(*) as n_dias
           from {{ ref('athlete_day') }} group by ID)
select m.*, rsa.BkMel, rsa.BkSoma, rsa.BkF, mdc.clsVigor, mdc.clsFadiga
from m left join {{ ref('rsa') }} rsa on m.ID = rsa.ID
       left join {{ ref('mdc') }} mdc on m.ID = mdc.ID
