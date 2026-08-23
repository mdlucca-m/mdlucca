with m as (select ID, avg(vigor) as vigor_med, avg(fadiga) as fadiga_med, avg(pth) as pth_med, count(*) as n_dias
           from {{ ref('athlete_day') }} group by ID)
select m.*, rsa.BkMel, rsa.BkSoma, rsa.BkF, mdc.clsVigor, mdc.clsFadiga
from m left join {{ ref('rsa') }} rsa on m.ID = rsa.ID
       left join {{ ref('mdc') }} mdc on m.ID = mdc.ID
