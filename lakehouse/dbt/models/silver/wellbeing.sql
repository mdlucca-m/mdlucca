select ID, cast(dia as int) as dia, avg(Epworth) as epworth, avg(PSS) as pss
from {{ source('bronze','wellbeing_raw') }} group by ID, dia
