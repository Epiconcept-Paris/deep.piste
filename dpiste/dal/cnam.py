import pandas as pd
import configparser
import os
import re
from datetime import datetime
import argparse
from pathlib import Path
from dpiste import utils as dputils
from dpiste import dal
#from dpiste import script_cnam
#from .. import script_cnam


def dummy_cnam_for_safe(dfs={}, lines = 1000):
  return cnam_dfs("dummy_cnam_for_safe", dfs)

def cnam_for_safe(dfs={}):
  return cnam_dfs("cnam_for_safe", dfs)

def create_random_df(lines = 100):
    """Generate a dummy dataframe with the same structure of real data with 1000 lines
    File structure : id_random, NNI_2, nom, nom_jf, prenom, date_naiss"""
    data = {'id_random':range(0, lines)}
    dfs = pd.DataFrame(data)
    dfs.index.rename('pk', inplace = True)
    dfs['NNI_2'] = ("2" + dfs['id_random'].astype(str)+ '12345678901234').str.slice(0, 13)
    dfs['nom'] = "nom"+dfs['id_random'].astype(str)
    dfs['nom_jf'] = "nom_jf"+dfs['id_random'].astype(str)
    dfs['prenom'] = "prenom"+dfs['id_random'].astype(str)
    dfs['date_naiss'] = pd.to_datetime('now').date() + pd.DateOffset(days=-20000)
    return dfs

def nir_to_cnam_format(df):
    """
       Adapt the screeening file to the CNAM expected format :
       Delete columns nom, nom_jf et prenom
       Rename NNI_2 as NIR_du_beneficiaire, date_naiss as Date_de_naissance
       Rename id_random as Identifiant_temporaire
       Move columns to obtain the followinf order NIR_du_beneficiaire|Date_de_naissance|Code_sexe|
       NIR_du_ouvrant_droit|Identifiant_temporaire
    """
    df = df[["id_random", "NNI_2", "date_naiss"]].copy()
    df.columns = ['Identifiant_temporaire','NIR_du_beneficiaire', 'Date_de_naissance'] #rename colums
    df['Date_de_naissance'] = df['Date_de_naissance'].dt.strftime("%m/%d/%Y") #convert date to JJ/MM/AAAA format
    df['NIR_du_ouvrant_droit'] = df['NIR_du_beneficiaire'].astype(str)
    df['Code_sexe'] = "2"
    df = df[['NIR_du_beneficiaire', 'Date_de_naissance', 'Code_sexe','NIR_du_ouvrant_droit','Identifiant_temporaire']]
    # Regarder dans neoscope.py la fonction neo_df. si il n'est pas créé le générer
    # sinon le créer
    return df

def cnam_path_transform(name):
    return dputils.get_home("data", "transform", "cnam",  f"{name}.parquet")

def cnam_path_transform_screening(name):
    return dputils.get_home("data", "transform", "screening", f"{name}.parquet")

def cnam_dfs(name,dfs={}):
    if(dfs.get(name) is not None):
      return df
    #elif os.path.exists(cnam_path_transform(name)):
    #  df=pd.read_parquet(cnam_path_transform(name))
    else:
        if name == "dummy_cnam_for_safe":
          df = create_random_df(25)
          df = nir_to_cnam_format(df)
        elif name == "cnam_for_safe":
          df = dal.screening.cnam(dfs)
          df = nir_to_cnam_format(df)
    #    df.to_parquet(cnam_path_transform(name), engine = "pyarrow")
    dfs[name]=df
    return df

