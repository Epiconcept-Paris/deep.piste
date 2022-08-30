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

def p06_001_get_dicom(server, port = 11112, retrieveLevel = 'STUDY', limit = None, page_size = 10, filter_field = None, filter_value = None):
  title = "DCM4CHEE"
  if filter_field == None and filter_value == None:
    log("No filter applied")
  else:
    log(f"Filter applied: {filter_field} = {filter_value}")
  studies = apply_filter(dal.screening.depistage_pseudo(), filter_field, filter_value)
 
  studies = studies.sort_values(by=['Date_Mammo'], ascending=False)
  uids = []
  uids_without_duplicates = set()
  for i, exam in enumerate(studies['DICOM_Studies']):
    dico = json.loads(exam)
    for k, v in dico.items():
        for uid in v[0]:
            if uid not in uids_without_duplicates:
                uids.append(uid)
                uids_without_duplicates.add(uid)

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
  return df[(df['L1_ACR_SG'] == '5') | (df['L1_ACR_SD'] == '5') | (df['L2_ACR_SG'] == '5') | (df['L2_ACR_SD'] == '5')]


def get_patient_random_id(df):
    shorten_df = df[['id_random', 'DICOM_Studies']]
    couples = []
    for i in shorten_df.index:
        uids_i = list(json.loads(shorten_df['DICOM_Studies'][i]).values())[0][0]
        couples.append((shorten_df['id_random'][i], uids_i))

    return couples
