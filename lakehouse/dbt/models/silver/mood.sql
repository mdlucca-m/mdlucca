with ranked as (
  select *, row_number() over (partition by ID, dia, seq order by _ingested_at desc) as rn
  from {{ source('bronze','brums_raw') }}
)
select ID, cast(dia as int) as dia, cast(seq as int) as seq, momento,
  cast(HIIT as int) as hiit_flag,
  case dia when 1 then 'Baseline' when 2 then 'HIIT' when 3 then 'Jogo'
           when 4 then 'HIIT' when 5 then 'Jogo' when 6 then 'Forca'
           when 7 then 'HIIT' end as day_type,
  Tensao, Depressao, Raiva, Vigor, Fadiga, Confusao, TMD as PTH, FadFisica, FadMental,
  (seq = min(seq) over (partition by ID, dia)) as is_pre,
  (seq = max(seq) over (partition by ID, dia)) as is_pos
from ranked where rn = 1
