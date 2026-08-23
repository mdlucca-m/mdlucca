with pre as (select ID, dia, Vigor as v_pre, Fadiga as f_pre, PTH as p_pre from {{ ref('mood') }} where is_pre),
     pos as (select ID, dia, Vigor as v_pos, Fadiga as f_pos, PTH as p_pos from {{ ref('mood') }} where is_pos)
select pre.ID, pre.dia, round(v_pos - v_pre,4) as d_vigor,
       round(f_pos - f_pre,4) as d_fadiga, round(p_pos - p_pre,4) as d_pth
from pre join pos using (ID, dia)
