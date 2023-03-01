import kskit
import time
import os
import math
import json
import kskit.crypto
import kskit.dicom
import pandas as pd
import numpy as np
from dpiste import report
from . import dal
from . import utils
from kskit.dicom.utils import log
from datetime import datetime

def p06_001_get_dicom(server, port = 11112, retrieveLevel = 'STUDY', limit = None, page_size = 10, filter_field = None, filter_value = None):
  title = "DCM4CHEE"
  if filter_field == None and filter_value == None:
    log("No filter applied")
  else:
    log(f"Filter applied: {filter_field} = {filter_value}")
  studies = apply_filter(dal.screening.depistage_pseudo(), filter_field, filter_value)
 
  studies = studies.sort_values(by=['Date_Mammo'], ascending=False)
  log(f"{len(studies)} studies found with applied filter")
  uids = []
  uids_without_duplicates = set()
  for i, exam in enumerate(studies['DICOM_Studies']):
    dico = json.loads(exam)
    for k, v in dico.items():
        for uid in v[0]:
            if uid not in uids_without_duplicates:
                uids.append(uid)
                uids_without_duplicates.add(uid)
  log(f"{len(studies)} results containing {len(uids)} unique studies")
  chunks = math.floor(len(uids) / page_size)
  pages = math.ceil(len(uids) / page_size)

  nb_studies = 0
  if limit is None:
    log("Extracting all Studies...")
  else:
    log(f"Extracting {limit} Studies...")
  for page in range(0, pages):
    chunk_uids = [uid for i, uid in enumerate(uids) if i % chunks == page - 1]

    for uid in chunk_uids:
      if limit is not None and nb_studies >= limit:
        break

      dest = utils.get_home('input', 'dcm4chee', 'dicom', uid)
      if limit is not None:
        if nb_studies < limit:
          if not os.path.exists(dest):
            os.makedirs(dest)
          kskit.dicom.get_dicom(key=uid, dest=dest, server=server, port=port, title=title, retrieveLevel=retrieveLevel, silent=True)
          nb_studies += 1
        else:
          break

      if limit is None:
        if not os.path.exists(dest):
          os.makedirs(dest)
        kskit.dicom.get_dicom(key=uid, dest=dest, server=server, port=port, title=title, retrieveLevel=retrieveLevel, silent=True)
        nb_studies += 1
      print(f"{nb_studies}/{len(uids)} retrieved")

  log("Producing consolidated dicom dataframe")
  dicom_dir = utils.get_home("input", "dcm4chee", "dicom")
  df = kskit.dicom.dicom2df.dicom2df(dicom_dir)

  log("Removing empty columns")
  df = remove_empty_columns(df)

  log("Saving dicom consolidated dataframe")
  dicomdf_dir = utils.get_home("input", "dcm4chee", "dicom_df", "")
  df.to_parquet(os.path.join(dicomdf_dir, str(page)), "pyarrow")


def apply_filter(df: pd.DataFrame, field: str = None, value: str = None) -> pd.DataFrame:
  """Applies a filter if field & value are not None else removes NA values"""
  if field is None and value is None:
    return df[pd.notna(df['DICOM_Studies'])]
  elif field == 'GET_ACR5':
    df = get_acr5(df)
    return df[pd.notna(df['DICOM_Studies'])]
  elif value == 'True':
    return df[(df[field] == True) & (pd.notna(df['DICOM_Studies']))]
  elif value == 'False':
    return df[(df[field] == False) & (pd.notna(df['DICOM_Studies']))]
  else:
    return df[(df[field] == value) & (pd.notna(df['DICOM_Studies']))]


def remove_empty_columns(df):
  """Remove columns where ALL values are None, null or NaN"""
  col2remove = []
  for col in df.columns:
    if df[~((df[col].isnull()) | (df[col] == 'None'))][col].nunique() == 0:
      col2remove.append(col)
  return df.drop(columns=col2remove)


def get_acr5(df):
  """
    Filters a pandas DataFrame containing DICOM studies information to keep only rows where the ACR level is 5.

    Args:
        df (pandas.DataFrame): The input DataFrame containing DICOM studies information.

    Returns:
        pandas.DataFrame: The filtered DataFrame, with only rows where the ACR level is 5.
    """
  return df[(df['L1_ACR_SG'] == '5') | (df['L1_ACR_SD'] == '5') | (df['L2_ACR_SG'] == '5') | (df['L2_ACR_SD'] == '5')]


def get_positive_studies_only(df):
  """
    Filter a pandas DataFrame containing DICOM studies information to keep only rows where
    the first or the second radiography reading is cancer positive.

    Args:
        df (pandas.DataFrame): The input DataFrame containing DICOM studies information.

    Returns:
        pandas.DataFrame: A new DataFrame containing only the rows where the first or the second
        radiography reading is cancer positive.
    """
  return df[df["L1L2_positif"] == True]


def get_patient_random_id(df):
    shorten_df = df[['id_random', 'DICOM_Studies']]
    couples = []
    for i in shorten_df.index:
        uids_i = list(json.loads(shorten_df['DICOM_Studies'][i]).values())[0][0]
        couples.append((shorten_df['id_random'][i], uids_i))

    return couples


def extract_positive_studies(server="127.0.0.1", port=11112, title="DCM4CHEE", retrieveLevel="STUDY"):
  utils.cleandir(utils.get_home('input', 'dcm4chee', 'dicom'))
  df = depistage_pseudo()
  df_with_study_id = filter_depistage_pseudo(df)
  df_with_study_id_and_lecture_results = calculate_l1_l2_result(df_with_study_id)
  df_with_positive_only = get_positive_studies_only(df_with_study_id_and_lecture_results)
  df_without_nan_study_ids = keep_only_studies_with_images(df_with_positive_only)
  nb_studies_retrieved = 0
  
  for study_id in df_without_nan_study_ids["DICOM_Study"]:
    dest = utils.get_home('input', 'dcm4chee', 'dicom', study_id)
    kskit.dicom.get_dicom(key=study_id, dest=dest, server=server, port=port, title=title, retrieveLevel=retrieveLevel, silent=True)
    nb_studies_retrieved += 1
    print(f"{nb_studies_retrieved}/{len(df_without_nan_study_ids)} queried")
  


def filter_depistage_pseudo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes NaN studies from the dataframe and splits the studies to keep only the ones 
    where the date equals the value in the 'Date_Mammo' column (~1 month).
    
    Args:
        df (pandas.DataFrame): DataFrame containing DICOM studies information.
    
    Returns:
        pandas.DataFrame: DataFrame with NaN studies removed and only studies where the date 
        equals the value in the 'Date_Mammo' column.
    """
    df = df[pd.notna(df['DICOM_Studies'])]
    df["DICOM_Study"] = df.apply(lambda row: get_dicom(row), axis=1)
    return df


def get_dicom(row: pd.Series) -> pd.Series:
    """
    Filters a DICOM studies Pandas Series to keep only the study IDs where the DICOM study date is equal to the 
    date in the 'Date_Mammo' column.

    Args:
        row (pd.Series): Pandas Series representing a row in the dataframe.
        date_mammo (str): Date of mammogram.

    Returns:
        Union[None, str]: Returns None if the DICOM study date is different than the 'Date_Mammo' column, else
        returns only the DICOM study ID.
    """
    dates = json.loads(row['DICOM_Studies'])
    study_id = None
    for k, v in dates.items():
        for study_id in v[0]:
            key_date = datetime.strptime(k, '%Y-%m-%d %H:%M:%S')
            key_date = key_date.replace(hour=0, minute=0, second=0)
            date_mammo = row["Date_Mammo"]
            month_delta = (date_mammo.year - key_date.year) * 12 + date_mammo.month - key_date.month
            if abs(month_delta) <= 1:
              return study_id
    return None


def get_higher_acr_lvl(df: pd.DataFrame, index: int) -> int:
    """
    Returns the higher ACR level found in the 4 columns L1_ACR_SD, L1_ACR_SG, L2_ACR_SD, and L2_ACR_SG for the given row index.

    Args:
        df (pd.DataFrame): The dataframe with 4 columns L1_ACR_SD, L1_ACR_SG, L2_ACR_SD, and L2_ACR_SG.
        index (int): The index of the row for which to find the higher ACR level.

    Returns:
        int: The higher ACR level found in the 4 columns for the given row index.
    """
    acr_lvls = [df['L1_ACR_SD'][index], df['L1_ACR_SG'][index], df['L2_ACR_SD'][index], df['L2_ACR_SG'][index]]
    normalized_acr_lvls = [int(acr_lvl) if not pd.isnull(acr_lvl) and acr_lvl.isnumeric() else 0 for acr_lvl in acr_lvls]
    return np.nanmax(normalized_acr_lvls)


def are_acr_lvls_positive(acr_lvls: list) -> list:
    normalized_acr_lvls = [int(acr_lvl) if not pd.isnull(acr_lvl) and acr_lvl.isnumeric() else 0 for acr_lvl in acr_lvls]
    return any([True if acr_lvl == 0 or acr_lvl > 2 else False for acr_lvl in normalized_acr_lvls])


def calculate_l1_l2_result(df: pd.DataFrame) -> pd.DataFrame:
    df['L1_Result'] = df.apply(lambda row: get_l1_result(row), axis=1)
    df['L2_Result'] = df.apply(lambda row: get_l2_result(row), axis=1)
    return df


def get_l1_result(row: pd.Series) -> pd.Series:
    return "positive" if is_l1_positive(row) else "negative"


def get_l2_result(row: pd.Series) -> pd.Series:
    return "positive" if is_l2_positive(row) else "negative"


def is_l1_positive(row: pd.Series) -> bool:
    return are_acr_lvls_positive([row['L1_ACR_SD'], row['L1_ACR_SG']])


def is_l2_positive(row: pd.Series) -> bool:
    return are_acr_lvls_positive([row['L2_ACR_SD'], row['L2_ACR_SG']])


def keep_only_studies_with_images(df: pd.DataFrame) -> pd.DataFrame:
    return df[pd.notna(df['DICOM_Study'])]


if __name__ == '__main__':
  extract_positive_studies(server="127.0.0.1", port=11112, title="DCM4CHEE", retrieveLevel="STUDY")