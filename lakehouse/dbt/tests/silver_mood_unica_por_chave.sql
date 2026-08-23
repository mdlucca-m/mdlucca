-- falha se houver duplicata em (ID, dia, seq)
select ID, dia, seq, count(*) as n
from {{ ref('mood') }} group by 1,2,3 having count(*) > 1
