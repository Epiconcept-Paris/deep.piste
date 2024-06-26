"""Patch for adding ImageViewCode (MLO or CC)"""

import os
import pandas as pd
import pydicom

from deidcm.dicom.deid_mammogram import gen_dicom_uid

from dpiste.dal.screening import depistage_pseudo
from dpiste.p08_mammogram_deidentification import build_studies
from dpiste.utils import (cleandir, log)
from dpiste.dicom.get_dicom import get_dicom

PATCH_HEADERS = [
    "StudyInstanceUID_0020000d",
    "SOPInstanceUID_0x00080018",
    "ImageLaterality_0x00200062",
    "ViewCodeSequence_0x00540220_CodeValue_0x00080100",
    "ViewCodeSequence_0x00540220_CodeMeaning_0x00080104",
    "ViewCodeSequence_0x00540220_CodingSchemeDesignator_0x00080102"
]


def run_patch(indir: str, batch_size: str, org_root: str, patch_filepath: str) -> None:
    """
    Orchestrate the patch workflow

    Args:
        indir: directory where studies are going to be extracted from the PACS
        batch_size: number of lines to write in the patch file at each cycle
        org_root: DICOM UID Prefix
        patch_filepath: filepath of the patch CSV file
    """
    cleandir(indir)

    studies = get_studies_df()
    try:
        last_study_uid = calculate_progress(patch_filepath)
        do_retrieve_progress = True
    except (FileNotFoundError, ValueError):
        init_patch_file(patch_filepath)
        last_study_uid = studies.index[0]
        do_retrieve_progress = False

    batch_mammograms_metadata = []
    for i, index in enumerate(studies.index):
        study_id = studies['study_id'][index]
        id_random = studies['id_random'][index]
        deid_study_id = gen_dicom_uid(id_random, study_id, org_root)

        if do_retrieve_progress:
            if last_study_uid != deid_study_id:
                continue
            else:
                do_retrieve_progress = False
                log(f"Restarting at {last_study_uid}")

        study_dir = os.path.join(indir, study_id)
        os.mkdir(study_dir)

        get_dicom(key=study_id, dest=study_dir, server='10.1.2.9', port=11112,
                  title='DCM4CHEE', retrieveLevel='STUDY', silent=False)

        mammograms_metadata = retrieve_mammograms_metadata(
            study_id, deid_study_id, id_random, indir, org_root)
        if mammograms_metadata:
            batch_mammograms_metadata.extend(mammograms_metadata)

        batch_mammograms_metadata = save_metadata(
            batch_mammograms_metadata, batch_size, patch_filepath)
        cleandir(indir)
        log(f"{study_id} => Added to batch")
        log(f"progress: {i}/{len(studies)} done")
    save_metadata(batch_mammograms_metadata, batch_size,
                  patch_filepath, force=True)


def init_patch_file(patch_filepath: str) -> None:
    """Create patch.csv and write CSV column headers"""
    headers_line = ",".join(PATCH_HEADERS) + "\n"
    with open(patch_filepath, mode="w", encoding="utf8") as f:
        f.write(headers_line)


def get_studies_df() -> pd.DataFrame:
    screening_df = depistage_pseudo()
    studies = build_studies(screening_df)
    return studies


def retrieve_mammograms_metadata(study_id: str, deid_study_id: str, id_random: str, indir: str, org_root: str) -> list:
    """Iterate the study's elements and retrieve specific information"""
    mammograms_metadata = []
    study_dir = os.path.join(indir, study_id)
    for mammogram_uid in os.listdir(study_dir):
        mammogram_file = os.path.join(study_dir, mammogram_uid)
        ds = pydicom.dcmread(mammogram_file)
        mammograms_metadata.append([
            deid_study_id,
            gen_dicom_uid(id_random, ds.SOPInstanceUID, org_root),
            ds.ImageLaterality,
            ds.ViewCodeSequence[0].CodeValue,
            ds.ViewCodeSequence[0].CodeMeaning,
            ds.ViewCodeSequence[0].CodingSchemeDesignator
        ])
    return mammograms_metadata


def add_metadata_to_patch_file(mammograms_metadata: list, patch_filepath: str) -> None:
    """Add retrieved information to patch.csv"""
    for mammogram_metadata in mammograms_metadata:
        metadata_line = ",".join(mammogram_metadata) + "\n"
        with open(patch_filepath, mode="a", encoding="utf8") as f:
            f.write(metadata_line)


def save_metadata(batch_mammograms_metadata: list, batch_size: int, patch_filepath: str, force: bool = False) -> list:
    """Decide whether or not patch.csv should be updated"""
    if len(batch_mammograms_metadata) >= batch_size or force:
        log("writing batch to file")
        add_metadata_to_patch_file(
            batch_mammograms_metadata, patch_filepath=patch_filepath)
        batch_mammograms_metadata = []
    return batch_mammograms_metadata


def calculate_progress(patch_filepath: str) -> str:
    """
    Retrieve the last StudyInstanceUID that has been processed
    completely or partially (in both cases, it will repeat the
    patching process for this study)
    """
    progress = 0
    try:
        with open(patch_filepath, "rb") as f:
            # Set the cursor a the end of the file and move
            # backwards until it meets \n character
            try:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            # One line file Error
            except OSError:
                f.seek(0)
            last_line_splitted = f.readline().decode().split(',')
    # File does not exist Error
    except IOError:
        raise FileNotFoundError(patch_filepath)

    last_study_uid = last_line_splitted[0]
    if not last_study_uid:
        raise ValueError("Cannot determine last StudyUID")

    if last_study_uid == PATCH_HEADERS[0]:
        raise ValueError("CSV file only contains headers")

    log(f"last study processed: {last_study_uid}")
    return last_study_uid


if __name__ == '__main__':
    run_patch(
        indir="/space/Work/william2/deep.piste/home/input/dcm4chee/indir_extract",
        batch_size=1000,
        org_root="replaceme",
        patch_filepath="/space/Work/william2/deep.piste/home/input/dcm4chee/patch.csv"
    )
