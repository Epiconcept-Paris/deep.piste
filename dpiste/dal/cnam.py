
def safe_test(dfs={}):
  return cnam_df("safe_test", dfs)

def safe(dfs={}):
  return cnam_df("safe", dfs)
  
def dummy_cnam(dfs={}):
  return cnam_df("dummy_cnam", dfs)

def cnam_path():
  raise NotImplementedError()

def cnam_dfs(name):
  if name == "safe_test":
    #source: dummy_cnam pour transformer en safe
    #action: transromer en safe
    #output: data/output/cnam/safe_test
    raise NotImplementedError()
  elif name = "safe":
    #source  dal.screening.cnam pour transformer en safe
    #  pour developpement il faut saugfgarder le fichier dummy_cnam dans data/transform/screening/cnam.parquet
    #action: transromer en safe
    #output: data/output/cnam/safe
    raise NotImplementedError()
  elif name == "dummy_cnam":
    raise NotImplementedError()
    
  # storing final dataset as the expected format
  if not os.path.exists(cnam_path(name)):
    #special case for safe is not parquet
    dfs[name].to_parquet(cnam_path(name), engine = "pyarrow")
  return dfs[name]

