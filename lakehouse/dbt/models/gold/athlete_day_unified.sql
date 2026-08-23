with hd as (
  select ID, case sessao when 'S1' then 2 when 'S2' then 4 when 'S3' then 7 end as dia,
    avg(PSE) as hiit_pse, avg(dFC) as hiit_dfc, max(FC_pos) as hiit_fcmax
  from {{ ref('hiit') }} group by 1, 2)
select ad.*, wb.epworth, wb.pss, hd.hiit_pse, hd.hiit_dfc, hd.hiit_fcmax
from {{ ref('athlete_day') }} ad
left join {{ ref('wellbeing') }} wb on ad.ID = wb.ID and ad.dia = wb.dia
left join hd on ad.ID = hd.ID and ad.dia = hd.dia
