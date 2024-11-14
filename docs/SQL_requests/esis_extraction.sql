select 
    p.num_bci person_id, 
    ex.date_mammo mammogram_date, 
    ap.date_heure appointment_date, 
    m.study_instance_uid, 
    m.dicom_study_id, 
    m.date_study, 
    d.file_guid, 
    ap.id_exam_center 
from ndmt_rdv_data ap 
    inner join ndmt_01_data p on p.id_data = ap.id_assure 
    left join ndmt_05_data ex on ap.id_lecture1 = ex.id_data 
    left join ndmt_sdy_data m on m.id_rdv = ap.id_data 
    left join ndmt_doc_data d on d.id_study = m.id_data 
    left join ndmt_examcenter_data c on c.id_data = ap.id_exam_center
where 
    p.num_bci is not null and c.postcode regexp '(^48.*)|(^30.*)’  
limit 10