select ID, sessao, fase, FC_pre, FC_pos, dFC, PSE
from (select *, row_number() over (partition by ID, sessao, fase order by _ingested_at desc) as rn
      from {{ source('bronze','hiit_raw') }}) where rn = 1
