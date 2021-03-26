import os
import pandas as pd
import numpy as np
from ..utils import get_home
from . import utils


def esis_pks(): return {"dicom_guid":["study_instance_uid"], "dicom_exams":["appointment_date", "person_id"]}

def dicom_guid(dfs={}):
  dfile = get_home("input", "esis",  "esis_dicom_guid.parquet")
  df = pd.read_parquet(dfile)
  df["person_id"] = df.person_id.map(lambda v: v if v != '' else pd.NA).astype("string").astype(pd.Int64Dtype())
  df["center_name"] = df.center_name.astype("string")
  df["dicom_study_id"] = df.dicom_study_id.astype("string")
  df["file_guid"] = df.file_guid.astype("string")
  df["study_instance_uid"] = df.study_instance_uid.astype("string")
  name = "dicom_guid"
  pk = esis_pks()[name]
  dfs[f"{name}_na"] = utils.get_na_rows(df, pk) 
  notna = utils.get_notna_rows(df, pk)
  dfs[f"{name}_dup"] = utils.get_dup_rows(notna, pk) 
  dfs[name] = utils.force_pk(df, pk)
  return dfs[name]

def dicom_exams(dfs={}):
  guid = dicom_guid(dfs)
  df = guid.groupby(["person_id", "appointment_date"]).study_instance_uid.apply(np.array).to_frame()
  name = "dicom_exams"
  dfs[name] = df
  return dfs[name]

def dicom_instance_uid():
  return (dicom_guid()
    .study_instance_uid
    .loc[lambda uid: uid != "None"]
    .unique()
  )

def dicom_df_files() :
  dicom_dir = get_home("input", "dcm4chee", "dicom_df")
  for root, dirs, files in os.walk(dicom_dir):
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
