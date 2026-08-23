select * exclude (_source, _load_id, _ingested_at, _row_hash, rn)
from (select *, row_number() over (partition by _row_hash order by _ingested_at desc) as rn
      from {{ source('bronze','brums_items_raw') }}) where rn = 1
