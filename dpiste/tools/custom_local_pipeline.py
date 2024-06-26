"""
This script aims at extracting studies according to a custom source file containing
a list of Study UIDs.
"""
import os
from datetime import datetime

import pandas as pd

from deidcm.dicom.df2dicom import df2dicom
from deidcm.dicom.deid_mammogram import deidentify_attributes

from dpiste.utils import cleandir
from dpiste.dicom.get_dicom import get_dicom

# Script Config

SOURCE_FILE_PATH = os.path.join(
    os.environ['DP_HOME'], 'data', 'input', 'epiconcept', 'source.csv')
SOURCE_FILE_ENCODING = 'utf8'

INDIR_EXTRACT = os.path.join(
    os.environ['DP_HOME'], 'data', 'transform', 'custom_local_pipeline')
ORG_ROOT = 'replaceme'

OUTDIR_DEID = os.path.join(
    os.environ['DP_HOME'], 'data', 'output', 'custom_local_pipeline')


def run() -> None:
    """
    1. Read a custom CSV file containing a list of studies to extract.
    2. Extract given studies from DCM4CHEE in INDIR_EXTRACT
    3. Deidentify mammograms from INDIR_EXTRACT to OUTDIR_EXTRACT
       (Image + Attributes) as DCM and PNG.    
    """
    studies_df = _prepare_source_file()
    os.makedirs(OUTDIR_DEID, exist_ok=True)

    for index in studies_df.index:
        cleandir(INDIR_EXTRACT)
        row = studies_df.loc[index]
        _process_study(row.source_study_id)

        if row.anteriorite == "Oui":
            _process_study(row.source_ant_study_id)

    studies_df.drop(columns=['source_study_id', 'source_ant_study_id'])


def _prepare_source_file() -> pd.DataFrame:
    """
    Read a custom CSV file containing a list of studies to extract
    and return the content as a dataframe.
    """
    df = pd.read_csv(SOURCE_FILE_PATH, encoding=SOURCE_FILE_ENCODING)

    df.sort_values(by='BCI', axis=0, ascending=True, inplace=True)
    df.BCI = [i for i in range(1, len(df.BCI) + 1)]
    df.rename(
        columns={
            "BCI": "idFemme",
            "Date MG Expér Inca": "DateMG",
            "Date MG Antériorité": "DateAntMG",
            "Antériorité": "anteriorite"
        },
        inplace=True
    )

    df['source_study_id'] = [id for id in df.study_id]
    df['source_ant_study_id'] = [id for id in df.ant_study_id]

    df.DateMG = [_reformat_date(date) for date in df.DateMG]
    df.DateAntMG = [_reformat_date(date) for date in df.DateAntMG]

    df.study_id = [f'{id}_{date}' for id, date in zip(df.idFemme, df.DateMG)]
    df.ant_study_id = [f'{id}_{date}' for id,
                       date in zip(df.idFemme, df.DateAntMG)]
    return df


def _reformat_date(str_date: str) -> str:
    date = datetime.strptime(str_date, '%d/%m/%y')
    return datetime.strftime(date, '%d%m%y')


def _process_study(study_id) -> None:
    """Extract and deidentify given study"""
    study_dir = os.path.join(INDIR_EXTRACT, study_id)
    deid_study_dir = os.path.join(OUTDIR_DEID, study_id)
    os.makedirs(study_dir, exist_ok=True)
    os.makedirs(deid_study_dir, exist_ok=True)

    get_dicom(key=study_id, dest=study_dir, server='10.1.2.9', port=11112,
              title='DCM4CHEE', retrieveLevel='STUDY', silent=False)

    study_df = deidentify_attributes(
        study_dir, deid_study_dir, ORG_ROOT, erase_outdir=False)
    df2dicom(study_df, deid_study_dir, do_image_deidentification=True,
             output_file_formats=["png", "dcm"])


if __name__ == '__main__':
    run()
