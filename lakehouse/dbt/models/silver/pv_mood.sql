-- Pares pico de velocidade (T-CAR) × humor, CASADOS na fonte (identidade real) e
-- emitidos já anonimizados como vetores paralelos (sem A-code nem P-code): a
-- fronteira de anonimização é respeitada — nenhuma junção fabricada entre esquemas.
-- Grão: par (1..25) × dimensão. Deduplica por (pair, dim) mantendo a última carga.
select pair, dim, cast(pv as double) as pv, cast(mood as double) as mood
from (select *, row_number() over (partition by pair, dim order by _ingested_at desc) as rn
      from {{ source('bronze','pv_mood_raw') }}) where rn = 1
