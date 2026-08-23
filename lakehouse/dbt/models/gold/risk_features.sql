with t as (
  select ID, dia, day_type, hiit_flag, vigor, fadiga, pth,
    quantile_cont(pth, 0.66) over () as thr,
    lead(pth) over (partition by ID order by dia) as pth_amanha
  from {{ ref('athlete_day') }})
select ID, dia, day_type, hiit_flag, vigor, fadiga, pth,
  case when pth_amanha is null then null when pth_amanha >= thr then 1 else 0 end as risco_amanha
from t
