import os
import pandas as pd
from ..utils import get_home

def dicom_guid():
  dfile = os.path.join(get_home(), "esis_dicom_guid.parquet")
  return pd.read_parquet(dfile)

def dicom_instance_uid():
  return (dicom_guid()
    .study_instance_uid
    .loc[lambda uid: uid != "None"]
    .unique()
  )

def dicom_df_files() :
  dicomdf_dir = os.path.join(get_home(), "dicom_df")
  for root, dirs, files in os.walk(dicomdf_dir):
    for file in files:
      yield os.path.join(root, file)

def dicom_df():
  return pd.concat(
    map(
      lambda f: pd.read_parquet(f),
      dicom_df_files()
    )
    , ignore_index = True
  )
