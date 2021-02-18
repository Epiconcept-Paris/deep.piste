import os
import pandas as pd
from ..utils import get_home

def dicom_guid():
  dfile = os.path.join(get_home(), "esis_dicom_guid.parquet")
  return pd.read_parquet(dfile)

