import pydicom
import os
import pandas as pd
import json
from datetime import datetime

from dpiste import utils
from dpiste.dal.screening import depistage_pseudo
from dpiste.p11_hdh_data_transfer import renew_sftp, get_all_studies, decrypt_whole_folder
from dpiste.p11_hdh_encryption import p11_decrypt_hdh
from dpiste.p08_mammogram_deidentification import p08_001_export_hdh, filter_screening

from kskit.dicom.get_dicom import get_dicom
from kskit.dicom.dicom2df import dicom2df
from kskit.dicom.utils import log
from dpiste.utils import get_home

TAG = '0x00181405'

def calculate_sum_given_tag(folder: str) -> int:
    """Reads all mammograms in a folder and calculate the sum of xray values"""
    s = 0
    for root, dirs, files in os.walk(folder):
        for file in files:
            fpath = os.path.join(root, file)
            meta = pd.read_csv(fpath)
            tag_full_name = list(filter(lambda x: x if TAG in x else None, meta.columns.values))

            if len(tag_full_name) != 1:
                raise ValueError(f'Too many values: {tag_full_name}')
            for i in meta.index:
                s += meta[tag_full_name[0]][i]
    return s


def get_studies(df: pd.DataFrame, folder: str) -> None:
    utils.cleandir(folder)
    studies = []
    for exam in df['DICOM_Studies']:
        dico = json.loads(exam)
        for k, v in dico.items():
            for uid in v[0]:
                key_date = datetime.strptime(k, '%Y-%m-%d %H:%M:%S')
                key_date = key_date.replace(hour=0, minute=0, second=0)

                if key_date in list(map(lambda d: datetime.strptime(str(d)[0:10], '%Y-%m-%d'), df['Date_Mammo'].values)):
                    studies.append(uid)
    studies = set(studies)
    for study_id in studies:
        get_dicom(key=study_id, dest=folder, server='10.1.2.9', port=11112,
            title='DCM4CHEE', retrieveLevel='STUDY', silent=True)

    return


def run(folder: str, verbose: True) -> None:
    #Deidentified part
    p08_001_export_hdh(
        sftph='procom2.front2',
        sftpu='HDH_deeppiste', 
        batch_size=200,
        sftp_limit=50,
        tmp_fol=get_home('data/input/dcm4chee/consistency_test/'),
        id_worker=0,
        nb_worker=1,
        org_root="2.25" # Derived DICOM UID Construction method (for tests only)
        reset_sftp=True,
        screening_filter=True,
        test=True
    )

    deid_studies_folder = os.path.join(folder, 'deid_studies')
    os.mkdir(deid_studies_folder) if not os.path.exists(deid_studies_folder) else utils.cleandir(deid_studies_folder)

    c, sftp = renew_sftp('procom2.front2', 'HDH_deeppiste')
    get_all_studies(sftp, deid_studies_folder, specific_file='meta.csv.gpg')
    decrypt_whole_folder(deid_studies_folder)

    s1 = calculate_sum_given_tag(deid_studies_folder)
    
    # Not deidentified part
    not_deid_studies_folder = os.path.join(folder, 'not_deid_studies')
    os.mkdir(not_deid_studies_folder) if not os.path.exists(not_deid_studies_folder) else utils.cleandir(not_deid_studies_folder)

    screening = depistage_pseudo()
    filtered_screening = filter_screening(screening)
    studies = get_studies(filtered_screening, not_deid_studies_folder)
    meta = dicom2df(not_deid_studies_folder)
    utils.cleandir(not_deid_studies_folder)
    meta.to_csv(os.path.join(not_deid_studies_folder, 'meta.csv'))
    s2 = calculate_sum_given_tag(not_deid_studies_folder)
    if s1 == s2 and verbose:
        log(f'Test passed! s1: {s1} == s2: {s2}')
    return s1, s2


if __name__ == '__main__':
    run(get_home('data/input/dcm4chee/consistency_test/'))
