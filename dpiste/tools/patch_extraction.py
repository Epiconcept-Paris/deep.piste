
from dpiste.dal.screening import depistage_pseudo
from dpiste.p08_mammogram_deidentification import build_studies
from dpiste.p06_mammogram_extraction import (
    get_positive_studies_only,
    filter_depistage_pseudo,
    keep_only_studies_with_images,
    calculate_l1_l2_result,
)
from dpiste.utils import cleandir, get_home

from kskit.dicom.get_dicom import get_dicom
from kskit.dicom.utils import log
from kskit.dicom.dicom2df import dicom2df
from kskit.dicom.deid_mammogram import gen_dicom_uid

import os
import pydicom
import time
import pandas as pd
import subprocess

POSITIVE_STUDY_DIR = "/space/Work/william2/deep.piste/home/input/dcm4chee/dicom_positive" 
PATCH_EXTRACT_DIR = "/space/Work/william2/deep.piste/home/input/dcm4chee/patch_extraction"


def extract_positive_studies_and_build_meta_patch(server="10.1.2.9", port=11112, title="DCM4CHEE", retrieveLevel="STUDY"):
  # Screening Filtering
  meta_patch_file = os.path.join(get_home('input', 'dcm4chee'), 'meta-patch.csv')
  df = depistage_pseudo()

  df_with_study_id = filter_depistage_pseudo(df)
  df_with_study_id_and_lecture_results = calculate_l1_l2_result(df_with_study_id)
  df_with_positive_only = get_positive_studies_only(df_with_study_id_and_lecture_results)
  studies = keep_only_studies_with_images(df_with_positive_only)

  # Init or Retrieve Meta Patch
  if not os.path.isfile(meta_patch_file):
    cleandir(get_home('input', 'dcm4chee', 'dicom_positive'))
    meta_patch = pd.DataFrame([], columns=['IdRandom', 'DeidentifiedStudyUID', 'DeidentifiedSOPInstanceUID', 'ViewCodeSequence-CodeValue', 'ImageLaterality'])
  else:
    meta_patch = pd.read_csv(meta_patch_file)

  for progress, study_id in enumerate(studies["DICOM_Study"]):
    if gen_dicom_uid('', study_id) in meta_patch['DeidentifiedStudyUID']:
      continue

    study_dir = get_home('input', 'dcm4chee', 'dicom_positive', study_id)
    try:
      os.mkdir(study_dir)
    except FileExistsError:
      cleandir(study_dir)

    # Study Extraction 
    get_dicom(key=study_id, dest=study_dir, server=server, port=port, title=title, retrieveLevel=retrieveLevel, silent=True)

    # Meta Patch Update
    study_row = studies[studies["DICOM_Study"] == study_id]["id_random"].tolist()
    meta_patch = add_study_to_meta_patch(study_dir, meta_patch, studies[studies["DICOM_Study"] == study_id]["id_random"].tolist()[0])
    meta_patch.to_csv(meta_patch_file) if progress % 10 == 0 else None
    
    cleandir(study_dir)
    print(f"{progress + 1}/{len(studies)} queried")


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
    p1 = subprocess.Popen(["ls", POSITIVE_STUDY_DIR], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["wc", "-l"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    mammograms_number = p2.communicate()[0].decode('utf8')

    nb_mammogram_retrieved = 0
    for root, dirs, files in os.walk(POSITIVE_STUDY_DIR):
        for study_dir in dirs:
            study_id = study_dir
            study_dir = os.path.join(root, study_dir)
            study_row = studies[studies["study_id"] == study_id]["id_random"].tolist()
            if len(study_row) > 1:
                print(f"Warning: study {study_id} has more than 1 row in df")
            elif len(study_row) == 0:
                print(f"Warning: study {study_id} has no row in df")
                continue
            meta_patch = add_study_to_meta_patch(study_dir, meta_patch, studies[studies["study_id"] == study_id]["id_random"].tolist()[0])
            nb_mammogram_retrieved += 1
            print(f"{nb_mammogram_retrieved}/{mammograms_number}")

    meta_patch.to_csv(os.path.join(PATCH_EXTRACT_DIR, "meta-patch.csv"), index=False)
    print(f"Meta Patch has been written at {PATCH_EXTRACT_DIR}")


def add_study_to_meta_patch(study_dir, meta_df, id_random):
    id_random = {"IdRandom": [id_random] }
    for dcm_file in os.listdir(study_dir):
        dcm_filepath = os.path.join(study_dir, dcm_file)
        ds = pydicom.dcmread(dcm_filepath)
        study_id = get_deidentified_study_id(os.path.basename(study_dir))
        dicom_uid = get_deidentified_dicom_id(ds)
        orientation = get_dicom_orientation(ds)
        new_row = pd.DataFrame.from_dict({**id_random, **study_id, **dicom_uid, **orientation})
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


def get_deidentified_study_id(study_id):
    study_id = gen_dicom_uid('', study_id)
    return { "DeidentifiedStudyUID": [study_id] }


def get_deidentified_dicom_id(ds):
    dicom_id = gen_dicom_uid('', ds["SOPInstanceUID"].value)
    return { "DeidentifiedSOPInstanceUID": [dicom_id] }


def deidentify_study_id(studies: pd.DataFrame) -> pd.DataFrame:
    """Deidentifies the column study_id of the DataFrame df"""
    for index in studies.index:
        study_id = studies['study_id'][index]
        id_random = studies['id_random'][index]
        studies.at[index, 'study_id'] = gen_dicom_uid(id_random, study_id)
    studies = studies.rename(columns={'study_id': 'study_pseudo_id'})
    return studies


if __name__ == '__main__':
    extract_positive_studies_and_build_meta_patch()
    