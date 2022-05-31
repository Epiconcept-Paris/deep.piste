import pandas as pd
import numpy as np
import os
from . import neoscope
from . import utils
from .. import utils as dputils

def refusing_list():
  path = dputils.get_home("data", "input", "crcdc", "refusing-list.csv")
  if os.path.exists(path):
    df = pd.read_csv(path, dtype = object)
  else :
    df = pd.DataFrame(columns = ["NIR", "Nom Famille"], dtype = object) 
  return df

def refusing_random_ids(dfs = {}):
  pop = neoscope.population_df(dfs = dfs)
  return pop[pop["NNI_2"].isin(refusing_list()["NIR"])]["id_random"].to_numpy()
  


