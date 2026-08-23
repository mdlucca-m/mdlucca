select * exclude (_source, _load_id, _ingested_at, _row_hash, rn)
from (select *, row_number() over (partition by ID order by _ingested_at desc) as rn
      from {{ source('bronze','mdc_raw') }}) where rn = 1
