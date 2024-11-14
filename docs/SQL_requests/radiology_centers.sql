select id_centre, num_centre, esis_id_centre, esis_date,nom
from centre
where (esis_id_centre is not null or esis_date is not null)