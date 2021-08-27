from . import dal
import pandas as pd
from . import utils as dputils
from . import script_cnam
from types import SimpleNamespace
import zipfile
import os

def p12_001_safe_test(date_depot, nom_projet, num_projet):
  file_name = dputils.get_home("data", "output", "cnam", "safe_test")
  conf = {
    "path2output" : file_name,
    "date_depot" : date_depot,
    "num_projet" : num_projet,
    "nom_projet" : nom_projet
  }
  script_cnam.generate_normed_file(dal.cnam.dummy_cnam_for_safe(),SimpleNamespace(**conf))

  with zipfile.ZipFile("{file_name}.zip".format(**locals()), 'w', compression =  zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(file_name, arcname="deep-piste-test.safe")
  os.remove(file_name)

def p12_002_safe(date_depot, nom_projet, num_projet):
  file_name = dputils.get_home("data", "output", "cnam", "safe")
  conf = {
    "path2output" : dputils.get_home("data", "output", "cnam", "safe"),
    "date_depot" : date_depot,
    "num_projet" : num_projet,
    "nom_projet" : nom_projet
  }
  script_cnam.generate_normed_file(dal.cnam.cnam_for_safe(),SimpleNamespace(**conf))
  with zipfile.ZipFile("{file_name}.zip".format(**locals()), 'w', compression =  zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(file_name, arcname="deep-piste-test.safe")
  os.remove(file_name)

def p12_003_safe_duplicates_to_keep():
  dest = dputils.get_home("data", "output", "cnam", "duplicates_to_keep.csv")
  df = dal.cnam.duplicates_to_keep()
  df.to_csv(dest, encoding='utf-8')
