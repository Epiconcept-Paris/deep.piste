select assure.num_ref, assure.id_assure, assure.id_bci, assure.NNI_2, assure.NNI_2_cle, assure.sexe, assure.nom, assure.nom_jf, assure.prenom, assure.date_naiss, assure.email, count(*)
from assure join ks using (id_assure)
where ks.date_mammo between "date1" and "date2"
group by 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11