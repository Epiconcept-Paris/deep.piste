import pandas as pd
import numpy as np
from . import utils
from . import neoscope
from . import esis

def depistage_pseudo(dfs): return screening_df("dépistage_pseudo")
def cnam(dfs): return screening_df("cnam")
def table_correspondance(dfs): return screening_df("table_correspondance")
def mail(dfs): return screening_df("mail")

def screening_pks(): return {"dépistage_pseudo":["id_random", "Date_Mammo_Dépistage"], "cnam":"NNI_2", "table_correspondance":"id_random", "mail":"email"}

def screening_df(name, dfs = {}): 
  if(dfs.get(name) is None):
    df = calculated_df(name, dfs)
    pk = out_pks()[name]
    dfs[f"{name}_na"] = utils.get_na_rows(df, pk) 
    notna = utils.get_notna_rows(df, pk)
    dfs[f"{name}_dup"] = utils.get_dup_rows(notna, pk) 
    dfs[name] = utils.force_pk(df, pk)
  return dfs[name]

def calculate_df(name, dfs = {}):
  if name == "table_correspondance":
    ret = neoscope.population_df(dfs)[["id_random", "id_bci"]]
  elif name == "cnam":
    # creating
    ret =  population_df(dfs)[[
      "id_random",
      "NNI_2",      
      "NNI_2_cle", 
      "sexe",
      "nom",
      "nom_jf",
      "prenom",
      "date_naiss",
    ]]
    ret = ret[pd.notna(ret["id_random"]) & pd.notna(ret["NNI_2"]) & pd.notna(ret["NNI_2_cle"])]
  elif name == "email":
    ret = neoscope.population_df(dfs)[["email"]]
    ret = mail[pd.notna(mail["email"])]
    ret = mail.drop_duplicates(inplace = False, ignore_index = True)
  elif name == "dépistage_pseudo":
    # Producing the joined dataframe
    ret = (
      neoscope.depistage_df(dfs)
        .join(other = neoscope.suivi_df(dfs), on = ["id_event"], how = "left", lsuffix = "_Dépistage", rsuffix= "_Suivi") 
        .join(other = neoscope.risque_df(dfs), on = "id_event_Dépistage", how = "left", rsuffix= "_Risque") 
        .join(other = neoscope.adicap_df(dfs), on = "k_adicap", how = "left", rsuffix= "_Adicap") 
        .join(other = neoscope.adicap_df(dfs), on = "k_adicap2", how = "left", rsuffix= "_Adicap2") 
        .join(other = neoscope.population_df(dfs), on = "id_bci_Dépistage", how = "left", rsuffix= "_Population") 
    )
    to_remove_cols = []
    for col in to_remove_cols:
      del joined[col]
  else:
    raise ValueError("{name} is not recognized as a neoscope callulated table")
  return ret
