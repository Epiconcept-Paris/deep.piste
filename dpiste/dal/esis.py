import os
import pandas as pd
import numpy as np
import json
from ..utils import get_home
from . import utils


def esis_pks(): return {"dicom_guid":["study_instance_uid", "appointment_date", "file_guid"], "dicom_exams":["appointment_date", "person_id"]}

def dicom_guid(dfs={}):
  name = "dicom_guid"
  if name not in dfs.keys():
    dfile = get_home("input", "esis",  "esis_dicom_guid.parquet")
    df = pd.read_parquet(dfile)
    df["person_id"] = df.person_id.map(lambda v: v if v != '' and v != 'None' else pd.NA).astype("string").astype(pd.Int64Dtype())
    df["center_name"] = df.center_name.map(lambda v: v if v != '' and v != 'None' else pd.NA).astype("string")
    df["dicom_study_id"] = df.dicom_study_id.map(lambda v: v if v != '' and v != 'None' else pd.NA).astype("string")
    df["file_guid"] = df.file_guid.map(lambda v: v if v != '' and v != 'None' else pd.NA).astype("string")
    df["study_instance_uid"] = df.study_instance_uid.map(lambda v: v if v != '' and v != 'None' else pd.NA).astype("string")
    pk = esis_pks()[name]
    dfs[f"{name}_na"] = utils.get_na_rows(df, pk) 
    notna = utils.get_notna_rows(df, pk)
    dfs[f"{name}_dup"] = utils.get_dup_rows(notna, pk) 
    dfs[name] = utils.force_pk(df, pk)
  return dfs[name]

def dicom_exams(dfs={}):
  name = "dicom_exams"
  if name not in dfs.keys():
    guid = dicom_guid(dfs)
    # grouping by date and person
    grouped = guid.groupby(["person_id", "appointment_date"])
    df = grouped.study_instance_uid.apply(np.array).to_frame()
    df["file_count"] = grouped.file_guid.apply(np.array).map(lambda arr: len(arr)) 
    df["study_instance_uid"] = df.study_instance_uid.map(lambda ids: list(set(ids)) if ids is not None else None)
    df["person_id"]= df.index.map(lambda i: i[0])
    df["appointment_date"]= df.index.map(lambda i: i[1])
    df.index.rename(["pk1", "pk2"], inplace = True)

    #grouping by person
    df["dicom_studies"] = list(map(lambda t: (t[0], (t[1], t[2])), zip(df.appointment_date.astype("string"), df.study_instance_uid, df.file_count)))
    person_exams = df.groupby("person_id").dicom_studies.apply(np.array).map(lambda i: json.dumps(dict(i))).astype("string").to_frame()
    person_exams["person_id"]= person_exams.index
    person_exams.index.rename("pk1", inplace = True)
    dfs[name] = person_exams
  return dfs[name]

def dicom_instance_uid():
  return (dicom_guid()
    .study_instance_uid
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
