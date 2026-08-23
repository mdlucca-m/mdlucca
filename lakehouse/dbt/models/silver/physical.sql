-- CORREÇÃO (dono dos dados): desenho de GRUPO ÚNICO; rótulo Controle/Experimental neutralizado
select * exclude (_source, _load_id, _ingested_at, _row_hash, rn),
       'unico' as grupo_estudo
from (select *, row_number() over (partition by id order by _ingested_at desc) as rn
      from {{ source('bronze','physical_raw') }}) where rn = 1
