"""Patch for adding ImageViewCode (MLO or CC)"""

import os
import pandas as pd
import pydicom

from kskit.dicom.get_dicom import get_dicom
from kskit.dicom.deid_mammogram import gen_dicom_uid

from dpiste.dal.screening import depistage_pseudo
from dpiste.p08_mammogram_deidentification import build_studies
from dpiste import utils

# Epiconcept DICOM prefix (see user manual)
# TODO: This org_root is a sample one. Replace it with the correct one before
# running the patch 
ORG_ROOT = "1.2.826.2.4.3667563.20.866"
BATCH_SIZE = 10
INDIR_EXTRACT = "/space/Work/william2/deep.piste/home/input/dcm4chee/indir_extract"
PATCH_FILE = "/space/Work/william2/deep.piste/home/input/dcm4chee/patch.csv"
PATCH_HEADERS = [
    "StudyInstanceUID_0020000d",
    "SOPInstanceUID_0x00080018",
    "ImageLaterality_0x00200062",
    "ViewCodeSequence_0x00540220_CodeValue_0x00080100",
    "ViewCodeSequence_0x00540220_CodeMeaning_0x00080104",
    "ViewCodeSequence_0x00540220_CodingSchemeDesignator_0x00080102"
]

def run_patch() -> None:
    """Orchestrate the patch workflow"""
    utils.cleandir(INDIR_EXTRACT)
    init_patch_file()
    studies = get_studies_df()
    batch_mammograms_metadata = []
    for i, index in enumerate(studies.index):
        study_id = studies['study_id'][index]
        id_random = studies['id_random'][index]
        study_dir = os.path.join(INDIR_EXTRACT, study_id)
        os.mkdir(study_dir)

        get_dicom(key=study_id, dest=study_dir, server='10.1.2.9', port=11112,
                  title='DCM4CHEE', retrieveLevel='STUDY', silent=False)
        
        mammograms_metadata = retrieve_mammograms_metadata(study_id, id_random)
        if mammograms_metadata:
            batch_mammograms_metadata.extend(mammograms_metadata)
        
        batch_mammograms_metadata = save_metadata(batch_mammograms_metadata)
        utils.cleandir(INDIR_EXTRACT)
        print(f"{study_id} => Added to patch file")
        print(f"progress: {i}/{len(studies)} done")
    save_metadata(batch_mammograms_metadata, force=True)


def init_patch_file() -> None:
    """Create patch.csv and write CSV column headers"""
    headers_line = ",".join(PATCH_HEADERS) + "\n"
    with open(PATCH_FILE, mode="w", encoding="utf8") as f:
        f.write(headers_line)


def get_studies_df() -> pd.DataFrame:
    screening_df = depistage_pseudo()
    studies = build_studies(screening_df)
    return studies


def retrieve_mammograms_metadata(study_id: str, id_random: str) -> list:
    """Iterate the study's elements and retrieve specific information"""
    mammograms_metadata = []
    study_dir = os.path.join(INDIR_EXTRACT, study_id)
    for mammogram_uid in os.listdir(study_dir):
        mammogram_file = os.path.join(study_dir, mammogram_uid)
        ds = pydicom.dcmread(mammogram_file)
        mammograms_metadata.append([
            gen_dicom_uid(id_random, ds.StudyInstanceUID, ORG_ROOT),
            gen_dicom_uid(id_random, ds.SOPInstanceUID, ORG_ROOT),
            ds.ImageLaterality,
            ds.ViewCodeSequence[0].CodeValue,
            ds.ViewCodeSequence[0].CodeMeaning,
            ds.ViewCodeSequence[0].CodingSchemeDesignator
        ])
    return mammograms_metadata


def add_metadata_to_patch_file(mammograms_metadata: list) -> None:
    """Add retrieved information to patch.csv"""
    for mammogram_metadata in mammograms_metadata:
        metadata_line = ",".join(mammogram_metadata) + "\n"
        with open(PATCH_FILE, mode="a", encoding="utf8") as f:
            f.write(metadata_line)


def save_metadata(batch_mammograms_metadata: list, force: bool=False) -> list:
    """Decide whether or not patch.csv should be updated"""
    if len(batch_mammograms_metadata) >= BATCH_SIZE or force:
        add_metadata_to_patch_file(batch_mammograms_metadata)
        batch_mammograms_metadata = []
    return batch_mammograms_metadata


if __name__ == '__main__':
    run_patch()
    