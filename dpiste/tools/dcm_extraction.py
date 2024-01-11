"""
A simple script for extracting from a PACS and storing mammograms inside
a local folder.
"""

import pandas as pd
import os
import pydicom

from kskit.dicom.get_dicom import get_dicom
from kskit.dicom.deid_mammogram import get_PIL_image 

from dpiste.dal.screening import depistage_pseudo
from dpiste.p08_mammogram_deidentification import build_studies

from dpiste.utils import cleandir 

INDIR_EXTRACT = os.path.join(os.environ['DP_HOME'], 'data', 'transform', 'removeme')
ORG_ROOT = 'replaceme'

OUTDIR_DEID = os.path.join(os.environ['DP_HOME'], 'data', 'output', 'removeme')


def run() -> None:
    studies = get_studies_df()

    for index in studies.index:
        cleandir(INDIR_EXTRACT)
        study_id = studies['study_id'][index]
        study_dir = os.path.join(INDIR_EXTRACT, study_id)
        deid_study_dir = os.path.join(OUTDIR_DEID, study_id)
        os.makedirs(study_dir, exist_ok=True)
        os.makedirs(deid_study_dir, exist_ok=True)

        get_dicom(key=study_id, dest=study_dir, server='10.1.2.9', port=11112,
                    title='DCM4CHEE', retrieveLevel='STUDY', silent=False)
        
        if len(os.listdir(study_dir)) <= 4:
            continue

        for file in os.listdir(study_dir):
            try:
                ds = pydicom.dcmread(os.path.join(study_dir, file))
                img = get_PIL_image(ds)
                img.save(os.path.join(deid_study_dir, f"{ds.SOPInstanceUID}.png"))
            except pydicom.errors.InvalidDicomError:
                print(f"cannot load image in {os.path.join(study_dir, file)}")
                continue
        input("> ")


def get_studies_df() -> pd.DataFrame:
    screening_df = depistage_pseudo()
    studies = build_studies(screening_df)
    return studies


if __name__ == '__main__':
    run()