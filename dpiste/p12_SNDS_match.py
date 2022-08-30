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

def p12_004_safe_file():
  file_name = dputils.get_home("data", "output", "cnam", "safe.zip")
  if os.path.exists(file_name):
    with zipfile.ZipFile(file_name) as zipf:
      with zipf.open('deep-piste-test.safe') as file:
        lines = file.readlines()[2:-2]
    nnis2, ids_random = [], []
    for line in lines:
      nni2, id_random = line.decode('utf-8').split()
      nnis2.append(nni2)
      ids_random.append(id_random)
    prefix = os.path.commonprefix(ids_random)
    ids_random = [int(id_random.replace(prefix, '')) for id_random in ids_random]
    nnis2 = [nni2[-13:] for nni2 in nnis2]
    data = {'pk': ids_random, 'NNI_2': nnis2, 'id_random': ids_random}
    print('Getting Safe file...')
    df = pd.DataFrame(data).set_index('pk')
    df['NNI_2'] = df['NNI_2'].astype(str)
  else:
    print('Getting CNAM Mapping file...')
    df = dal.screening.cnam(dfs0)
  return df


