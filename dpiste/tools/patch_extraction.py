
from dpiste.dal.screening import depistage_pseudo
from dpiste.p08_mammogram_deidentification import build_studies
from dpiste.utils import cleandir

from kskit.dicom.get_dicom import get_dicom
from kskit.dicom.utils import log
from kskit.dicom.dicom2df import dicom2df
from kskit.dicom.deid_mammogram import gen_dicom_uid

import os
import pydicom
import time
import pandas as pd
import subprocess

ACR5_STUDIES_DIR = "/space/Work/william2/deep.piste/home/data/input/dcm4chee/dicom_acr5" 
PATCH_EXTRACT_DIR = "/space/Work/william2/deep.piste/home/data/patch_extraction"

def get_studies_and_patch_meta_files():
    df = depistage_pseudo()
    studies = build_studies(df)
    
    meta_patch = pd.DataFrame([], columns=[
        'IdRandom',
        'SOPInstanceUID',
        'ViewCodeSequence-CodeValue',
        'ImageLaterality',
        ]
    )
    p1 = subprocess.Popen(["ls", ACR5_STUDIES_DIR], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["wc", "-l"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    mammograms_number = p2.communicate()[0].decode('utf8')

    nb_mammogram_retrieved = 0
    for root, dirs, files in os.walk(ACR5_STUDIES_DIR):
        for study_dir in dirs:
            study_id = study_dir
            study_dir = os.path.join(root, study_dir)
            meta_patch = add_study_to_meta_patch(study_dir, meta_patch, studies[studies["study_id"] == study_id]["id_random"].tolist()[0])
            nb_mammogram_retrieved += 1
            print(f"{nb_mammogram_retrieved}/{mammograms_number}")
    print(meta_patch.columns)
    meta_patch.to_csv(os.path.join(PATCH_EXTRACT_DIR, "meta-patch.csv"), index=False)
    print(f"Meta Patch has been written at {PATCH_EXTRACT_DIR}")


def add_study_to_meta_patch(study_dir, meta_df, id_random):
    id_random = {"IdRandom": [id_random] }
    for dcm_file in os.listdir(study_dir):
        dcm_filepath = os.path.join(study_dir, dcm_file)
        ds = pydicom.dcmread(dcm_filepath)
        dicom_uid = get_deidentified_dicom_id(ds)
        orientation = get_dicom_orientation(ds)
        new_row = pd.DataFrame.from_dict({**id_random, **dicom_uid, **orientation})
        meta_df = pd.concat([meta_df, new_row], ignore_index=True)
    return meta_df

def get_dicom_orientation(ds):
    if "ViewCodeSequence" not in ds:
        position = "UNKNOWN"
    else:
        position = ds["ViewCodeSequence"][0]["CodeValue"].value

    if "ImageLaterality" not in ds:
        laterality = "UNKNOWN"
    else:
        laterality = ds["ImageLaterality"].value
    return { 
        "ViewCodeSequence-CodeValue": [position],
        "ImageLaterality": [laterality]
    }


def get_deidentified_dicom_id(ds):
    dicom_id = gen_dicom_uid('', ds["SOPInstanceUID"].value)
    return { "SOPInstanceUID": [dicom_id] }


def deidentify_study_id(studies: pd.DataFrame) -> pd.DataFrame:
    """Deidentifies the column study_id of the DataFrame df"""
    for index in studies.index:
        study_id = studies['study_id'][index]
        id_random = studies['id_random'][index]
        studies.at[index, 'study_id'] = gen_dicom_uid(id_random, study_id)
    studies = studies.rename(columns={'study_id': 'study_pseudo_id'})
    return studies

if __name__ == '__main__':
    #add_view_code_sequence_to_meta("/space/Work/william2/deep.piste/home/data/input/dcm4chee/dicom_positive/1.2.826.0.1.3680043.2.455.30.10.762000.1710.707536")
    #get_studies_and_patch_meta_files()
    get_studies_and_patch_meta_files()
    