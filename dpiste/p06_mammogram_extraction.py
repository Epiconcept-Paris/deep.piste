import kskit
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

def p06_001_get_dicom(server, port = 11112, retrieveLevel = 'STUDY', limit = 100, page_size = 10, filter_field = None, filter_value = None):
  title = "DCM4CHEE"
  print(filter_field)
  print(filter_value)
  studies = apply_filter(dal.screening.depistage_pseudo(), filter_field, filter_value)
  
  #print(studies.columns)
  studies = studies.sort_values(by=['Date_Mammo'], ascending=False)
  print(get_patient_random_id(studies))
  uids = []
  for i, exam in enumerate(studies['DICOM_Studies']):
    dico = json.loads(exam)
    for k, v in dico.items():
      uids.extend(v[0])
  chunks = math.floor(len(uids) / page_size)
  pages = math.ceil(len(uids) / page_size)
  #print(uids)
  i_dicom = 0
  for page in range(0, pages):
    chunk_uids = [uid for i, uid in enumerate(uids) if i % chunks == page - 1]
    #print(chunk_uids)
    print("getting dicoms")
    for uid in chunk_uids:
      if i_dicom <= limit:
        dest = utils.get_home("input", "dcm4chee", "dicom", uid)
        if not os.path.exists(dest):
            os.makedirs(dest)
        kskit.dicom.get_dicom(key = uid, dest = dest, server = server, port = port, title = title, retrieveLevel = retrieveLevel)
        i_dicom += 1
      else:
        break
    if i_dicom >= limit:
      break

  print("producing consolidated dicom dataframe")
  dicom_dir = utils.get_home("input", "dcm4chee", "dicom")
  df = kskit.dicom.dicom2df(dicom_dir)

  print("Saving dicom consolidated dataframe")
  dicomdf_dir = os.path.join("input", "dcm4chee", "dicom_df")
  df.to_parquet(os.path.join(dicomdf_dir, str(page)), "pyarrow")

def apply_filter(df: pd.DataFrame, field: str = None, value: str = None) -> pd.DataFrame:
  """Applies a filter if field & value are not None else removes NA values"""
  if field is None and value is None:
    return df[pd.notna(df['DICOM_Studies'])]
  elif value == 'True':
    return df[(df[field] == True) & (pd.notna(df['DICOM_Studies']))]
  else:
    return df[(df[field] == value) & (pd.notna(df['DICOM_Studies']))]

def get_dicom(server, port = 11112, retrieveLevel = 'STUDY', page = 1, page_size = 10, filter = {}):
    """Même chose que la fonction du dessus mais avec un filtre
    """

def get_patient_random_id(df):
    shorten_df = df[['id_random', 'DICOM_Studies']]
    couples = []
    for i in shorten_df.index:
        uids_i = list(json.loads(shorten_df['DICOM_Studies'][i]).values())[0][0]
        couples.append((shorten_df['id_random'][i], uids_i))

    return couples
