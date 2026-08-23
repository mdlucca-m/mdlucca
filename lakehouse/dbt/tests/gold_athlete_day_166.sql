-- falha se o número de atleta-dias não for 166
select count(*) as n from {{ ref('athlete_day') }} having count(*) <> 166
