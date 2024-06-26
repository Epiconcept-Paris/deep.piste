"""Calculate the time the whole extraction process would take"""

import time
import pandas as pd

from dpiste.dicom.get_dicom import get_dicom
from dpiste.dal.screening import depistage_pseudo
from dpiste.p08_mammogram_deidentification import build_studies
from dpiste import utils

DEST_FOLDER = "/space/Work/william2/deep.piste/home/removeme"
NB_SAMPLES = 5


def seconds_to_days(seconds):
    seconds_per_day = 24 * 60 * 60
    days = seconds / seconds_per_day
    return days


def get_studies_df() -> pd.DataFrame:
    screening_df = depistage_pseudo()
    studies = build_studies(screening_df)
    return studies


def time_extraction_of_all_mammograms() -> None:
    studies = get_studies_df()
    start_time = time.time()

    # Function to evaluate
    extract_n_studies(studies)

    end_time = time.time()
    elapsed_time_seconds = end_time - start_time
    print(f"{NB_SAMPLES} studies took {elapsed_time_seconds:.2f} seconds (= {elapsed_time_seconds/60:.2f} minutes)")
    calculated_time_seconds = elapsed_time_seconds * \
        len(studies.index) / NB_SAMPLES
    print(f"{len(studies.index)} studies would take {calculated_time_seconds:.2f} seconds (= {calculated_time_seconds/60:.2f} minutes)")
    print(f"{len(studies.index)} studies would take {seconds_to_days(calculated_time_seconds):.2f} days")


def extract_n_studies(studies: pd.DataFrame) -> None:
    for index in studies.index[:NB_SAMPLES]:
        study_id = studies['study_id'][index]

        get_dicom(key=study_id, dest=DEST_FOLDER, server='10.1.2.9', port=11112,
                  title='DCM4CHEE', retrieveLevel='STUDY', silent=False)


if __name__ == '__main__':
    time_extraction_of_all_mammograms()
    utils.cleandir(DEST_FOLDER)
