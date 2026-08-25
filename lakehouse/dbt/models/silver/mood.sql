-- REGRA DO ESTUDO (dono dos dados): observação VÁLIDA por atleta-dia =
--   pré = primeira resposta da manhã (seq mínima) e pós = última do dia (seq máxima).
--   As respostas intermediárias ("mid") e pré/pós repetidos são duplas/erradas -> descartadas.
--   D1 (21/04) é BASELINE: conta apenas a medida da manhã (pré); a pós de D1 é descartada.
--   Resultado: 286 observações válidas = 27 baseline + 139 pré + 120 pós · 13 coletas.
with ranked as (
  select *, row_number() over (partition by ID, dia, seq order by _ingested_at desc) as rn
  from {{ source('bronze','brums_raw') }}
),
flagged as (
  select ID, cast(dia as int) as dia, cast(seq as int) as seq, momento,
    cast(HIIT as int) as hiit_flag,
    case dia when 1 then 'Baseline' when 2 then 'HIIT' when 3 then 'Jogo'
             when 4 then 'HIIT' when 5 then 'Jogo' when 6 then 'Forca'
             when 7 then 'HIIT' end as day_type,
    Tensao, Depressao, Raiva, Vigor, Fadiga, Confusao, TMD as PTH, FadFisica, FadMental,
    (seq = min(seq) over (partition by ID, dia)) as is_pre,
    (seq = max(seq) over (partition by ID, dia)) as is_pos
  from ranked where rn = 1
)
select ID, dia, seq,
  case when is_pre then 'pre' else 'pos' end as momento,   -- rótulo = endpoint (seq)
  hiit_flag, day_type,
  Tensao, Depressao, Raiva, Vigor, Fadiga, Confusao, PTH, FadFisica, FadMental,
  is_pre, is_pos
from flagged
where (is_pre or is_pos)                        -- endpoints válidos (pré/pós)
  and not (dia = 1 and is_pos and not is_pre)   -- D1 = só baseline (descarta pós de D1)
