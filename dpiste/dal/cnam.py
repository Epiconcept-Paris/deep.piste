import pandas as pd
import configparser
import os
import re
from datetime import datetime
import argparse
from pathlib import Path
import csv
from dpiste import utils as dputils
from dpiste import dal
#from dpiste import script_cnam
#from .. import script_cnam


def dummy_cnam_for_safe(dfs={}, lines = 1000):
  return cnam_dfs("dummy_cnam_for_safe", dfs)

def cnam_for_safe(dfs={}):
  return cnam_dfs("cnam_for_safe", dfs)

def create_random_df(lines = 1000):
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
    df.pop('nom')
    df.pop('nom_jf')
    df.pop('prenom')
    df.columns = ['Identifiant_temporaire','NIR_du_beneficiaire', 'Date_de_naissance'] #rename colums
    df['Date_de_naissance'] = df['Date_de_naissance'].dt.strftime("%m/%d/%Y") #convert date to JJ/MM/AAAA format
    df['NIR_du_ouvrant_droit'] = df['NIR_du_beneficiaire'].astype(str)
    df['Code_sexe'] = "2"
    df = df[['NIR_du_beneficiaire', 'Date_de_naissance', 'Code_sexe','NIR_du_ouvrant_droit','Identifiant_temporaire']]
    df.to_csv(cnam_path_transform("test_cnam"), sep=";", index = False)
    # Regarder dans neoscope.py la fonction neo_df. si il n'est pas créé le générer
    # sinon le créer
    return df

def cnam_path_transform(name):
    return dputils.get_home("transform", f"{name}.csv")

def cnam_path_transform_screening(name):
    return dputils.get_home("transform", "screening", f"{name}.parquet")

def cnam_path_output(name):
    return dputils.get_home("output", "safe", f"{name}.parquet")

def cnam_dfs(name,dfs={}):
    if(dfs.get(name) is not None):
      return df
    elif os.path.exists(cnam_path_transform(name)):
      #special case for safe is not parquet
      df=pd.read_parquet(cnam_path_transform(name))

    else:
        if name == "dummy_cnam_for_safe":
     #objectif ici ? générer le dummy en .parquet ?
     # retourne le dataframe et le stocke en .csv. stockage au format parquet non nécessaire. Fichier peu volumineux 1000 lignes
          df = create_random_df()
          nir_to_cnam_format(df)
        elif name == "cnam_for_safe":
          df=dal.screening.cnam()
          nir_to_cnam_format(df)
        df.to_parquet(cnam_path_transform(name), engine = "pyarrow")
    dfs[name]=df
    return df

"""
  if name == "safe_test":
    #source: dummy_cnam pour transformer en safe
    #action: transromer en safe
    #output: data/output/cnam/safe_test --> 01/07 :  On retourne plutôt le dataframe nécessaire à la cNAM

    #path2nirlist = chemin_emplacment_crea
    #path2nirlist = chemin_list_nir
    args = script_cnam.parse_args()
    conf = script_cnam.Config(args)
    #"path2nirlist" : dputils.get_home("transform","test_cnam.csv")

    return dfs[name]

  elif name == "safe":
    #source  dal.screening.cnam pour transformer en safe
    #  pour developpement il faut saugfgarder le fichier dummy_cnam dans data/transform/screening/cnam.parquet
    #action: transromer en safe
    #output: data/output/cnam/safe
    args = script_cnam.parse_args()
    conf = script_cnam.Config(args)
    # avoir un fichier parquet cnam.parquet dans transform/screening DONE
    #puis ajouter une étape pour sauvegarder le fichier au format csv qui sera utilisé ici :
    nirlist_parquet =  dputils.get_home("transform","screening","cnam.parquet")
    #print(nirlist_parquet)
    conf.path2nirlist = dputils.get_home("transform","screening","cnam.csv")
    conf.path2output = dputils.get_home("output","cnam", "safe")
    conf.date_depot = datetime.today().strftime('%d/%m/%Y')
    conf.num_projet = "799" # à modifier
    conf.nom_projet = "DP799"  # à modifier
    with open(conf.path2nirlist, 'r') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.readline(),delimiters=[',',';','|'])
        delimiter = dialect.delimiter
    nir_list = pd.read_csv(
                    conf.path2nirlist,
                    sep=delimiter,
                    dtype='string'
                    )
    script_cnam.generate_normed_file(nir_list,conf)
"""
