from . import dal
import pandas as pd

def p13_001_dummy_cnam_extraction(lines = 100):
  """Generate a dummy version of CNAM data file"""
  data = {'id_random':range(0, lines)}
  dfcnam = pd.DataFrame(data)
  dfcnam.index.rename('pk', inplace = True)
  dfcnam['NNI_2'] = ("2" + dfcnam['id_random'].astype(str)+ '12345678901234').str.slice(0, 13)
  dfcnam['nom'] = "nom"+dfcnam['id_random'].astype(str)
  dfcnam['nom_jf'] = "nom_jf"+dfcnam['id_random'].astype(str)
  dfcnam['prenom'] = "prenom"+dfcnam['id_random'].astype(str)
  dfcnam['date_naiss'] = pd.to_datetime('now').date() + pd.DateOffset(days=-20000)
  return dfcnam

  


