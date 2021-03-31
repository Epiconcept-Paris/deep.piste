import pandas as pd
import numpy as np
import zipfile
import datetime
from . import utils
from .. import utils as dputils


def source_pks(): return {"population":"id_bci", "risque":"id_event", "dépistage":"id_event", "suivi":"id_event", "adicap":"code_adicap", "cim":"id_centre"}
def source_fks(): 
  return  [
    {"fktable":"suivi", "fkcol":"id_event", "pktable":"dépistage"},
    {"fktable":"suivi", "fkcol":"k_adicap", "pktable":"adicap"},
    {"fktable":"suivi", "fkcol":"k_adicap2", "pktable":"adicap"},
    {"fktable":"risque", "fkcol":"id_event", "pktable":"dépistage"},
    {"fktable":"dépistage", "fkcol":"id_bci", "pktable":"population"}
  ]

def neo_df(name, dfs = {}): 
  if(dfs.get(name) is None):
    df = read_source_csv(name)
    pk =  source_pks()[name]
    dfs[f"{name}_na"] = utils.get_na_rows(df, pk) 
    notna = utils.get_notna_rows(df, pk)
    dfs[f"{name}_dup"] = utils.get_dup_rows(notna, pk) 
    dfs[name] = utils.force_pk(df, pk)
  return dfs[name]

def neo_dfs(dfs = {}):
  population_df(dfs)
  risque_df(dfs)
  depistage_df(dfs)
  suivi_df(dfs)
  adicap_df(dfs)
  # Validating foreign keys
  utils.check_fks(dfs = dfs, fks = source_fks(), pks = source_pks())
  return dfs

def population_df(dfs = {}): 
  # adding random ids on population dataset
  neo_df("population", dfs)["id_random"] = np.random.permutation(neo_df("population", dfs).shape[0])
  return neo_df("population", dfs)

def risque_df(dfs = {}): return neo_df("risque", dfs)
def depistage_df(dfs = {}): return neo_df("dépistage", dfs)
def suivi_df(dfs = {}): return neo_df("suivi", dfs)
def adicap_df(dfs = {}): return neo_df("adicap", dfs)

def get_archive_entry(name, archive):
  #Getting expected filenames from zip files
  for path in archive.namelist():
    if name == "population" and path.lower().endswith("population.csv"):
      return path
    elif name == "risque" and path.lower().endswith("risque ks.csv"):
      return path
    elif name =="dépistage" and path.lower().endswith("dépistages.csv"):
      return path
    elif name == "suivi" and path.lower().endswith("suivi.csv"):
      return path
    elif name == "adicap" and path.lower().endswith("adicap ks.csv"):
      return path
    elif name == "cim" and path.lower().endswith("liste cim.csv"):
      return path
  raise ValueError(f"Cannot find file for {name} in neoscope archive") 

def date_parser(d):
  if type(d) == str:
    return datetime.datetime.strptime(d, "%d/%m/%Y")
  elif np.isnan(d):
    return pd.NaT 
  else:
    raise ValueError(f"cannot paser {d} of type {type(d)} as date")

def read_source_csv(name):
  dputils.log(f"reading CSV {name}")
  with zipfile.ZipFile(dputils.get_home("input", "neo", "extraction_neoscope.zip"), "r") as archive:
    path = get_archive_entry(name, archive)
    parse_dates = []
    dtype = {}
    b_cols = []
    a_cols = []
    n_cols = []
    to_boolean_cols = []
    rename = {}
    if name=="population":
      dtype = {
        "NNI_2":"string",      
        "NNI_2_cle":"string", 
        "sexe":"string",
        "nom":"string",
        "nom_jf":"string",
        "prenom":"string",
        "email":"string",
      }
      parse_dates = [ "date_naiss"]
      rename = {"count(*)":"count"}
    elif name=="risque":
      dtype = {"Age_Mammo":"float", "id_event":pd.Int64Dtype()}
      parse_dates = ["Date_Mammo"]
      b_cols = ["THS", "ATCD_Cancer","ATCD_Cancer_Bilateral", "ATCD_Chir_Esth", "ATCD_Famil_Mere", "ATCD_Famil_Soeur", "ATCD_Famil_Fille", "ATCD_Famil_Autre"]
      a_cols = ["Age_Mammo","Age_ATCD_Cancer","Age_ATCD_Cancer_Bilateral", "Age_ATCD_Chir_Esth", "Age_ATCD_Famil_Mere", "Age_ATCD_Famil_Soeur", "Age_ATCD_Famil_Fille", "Age_ATCD_Famil_Autre"]        
    elif name=="dépistage":
      dtype = {
        "Id_event":pd.Int64Dtype(), 
        "BDI_ACR_SD":"string", 
        "BDI_ACR_SG":"string", 
        "L1_ACR_SG":"string", 
        "L1_ACR_SD":"string", 
        "L2_ACR_SD_SD":"string", 
        "L2_ACR_SD_SG":"string",
        "BDI":"string" 
      }
      parse_dates = ["Date_Mammo"]
      b_cols = ["resultat_global_L1L2"]
      to_boolean_cols = [
        {"col":"BDI", "to":{"Bilan immédiat nécessaire":"BDI", "Pas de BDI":pd.NA}},
        {"col":"comparaison_SD", "to":{"anomalie SD plus suspecte":"comparaison_SD_plus_suspecte"}},
        {"col":"comparaison_SG", "to":{"anomalie SG plus suspecte":"comparaison_SG_plus_suspecte"}},
        {"col":"ECS", "to":{"Normal":"Examen_Clinique_Sein_Normal", "Anormal":"Examen_Clinique_Sein_Anormal", "Refusé":"Examen_Clinique_Sein_Refus"}},
        {"col":"Echo_L1", "to":{"Echo réalisé sur mammo négative":"Echo_L1_Negative", "Non":pd.NA}},
        {"col":"Echo_ECS_L1_Suspecte", "to":{"Echo_L1_Suspecte":"Echo_L1_Suspecte", "Non":pd.NA}},
        {"col":"BDI_Agrandissement", "to":{"BDI_Agrandissement":"BDI_Agrandissement", "Non":pd.NA}},
        {"col":"BDI_Cytoponction", "to":{"BDI_Cytoponction":"BDI_Cytoponction", "Non":pd.NA}},
        {"col":"BDI_Echographie", "to":{"BDI_Echographie":"BDI_Echographie", "Non":pd.NA}},
        {"col":"BDI_CAT_Surveillance", "to":{"Surveillance":"L1_Conduite_a_tenir_Surveillance", "Non":pd.NA}},
        {"col":"BDI_CAT_Cytoponction", "to":{"Exam_Cytoponction":"L1_Conduite_a_tenir_Cytoponction", "Non":pd.NA}},
        {"col":"BDI_CAT_Microbiopsie", "to":{"Exam_Microbiopsie":"L1_Conduite_a_tenir_Microbiopsie", "Non":pd.NA}},
        {"col":"BDI_CAT_Macrobiopsie", "to":{"Exam_Macrobiopsie":"L1_Conduite_a_tenir_Macrobiopsie", "Non":pd.NA}},
        {"col":"BDI_CAT_AutrePEC", "to":{"Autre Prise en Charge":"L1_Conduite_a_tenir_Autre", "Non":pd.NA}},
        {"col":"L2_CAT_Surveillance", "to":{"Surveillance":"L2_Conduite_a_tenir_Surveillance", "Non":pd.NA}},
        {"col":"L2_CAT_Cytoponction", "to":{"Exam_Cytoponction":"L2_Conduite_a_tenir_Cytoponction", "Non":pd.NA}},
        {"col":"L2_CAT_Microbiopsie", "to":{"Exam_Microbiopsie":"L2_Conduite_a_tenir_Microbiopsie", "Non":pd.NA}},
        {"col":"L2_CAT_Macrobiopsie", "to":{"Exam_Macrobiopsie":"L2_Conduite_a_tenir_Macrobiopsie", "Non":pd.NA}},
        {"col":"L2_CAT_AutrePEC", "to":{"Autre Prise en Charge":"L2_Conduite_a_tenir_Autre", "Non":pd.NA}}
      ]
      n_cols = ["L1_Type_Image_SD", "L1_Type_Image_SG", "BDI_Type_Image_SG", "BDI_Type_Image_SD", "L2_Type_Image_SD", "L2_Type_Image_SG"]
      rename = {"L2_ACR_SD_SD":"L2_ACR_SD", "L2_ACR_SD_SG":"L2_ACR_SG", "Id_event":"id_event"}
    elif name=="suivi":
      dtype = {"id_event":pd.Int64Dtype(), "pT": "string", "pN": "string", "localisation":"string", "k_adicap":"string", "k_adicap2":"string", "Grade_SBR":"string"}
      parse_dates = ["Date_Mammo", "Date_Anapath", "Date_Inter_Chir", "Date_Radi", "Date_Horm", "Date_Chim"]
      n_cols = ["M", "Si_Malin", "Si_Benin"]
      to_boolean_cols = [
        {"col":"KS_Confirme", "to":{"KS_confirmé":"KS_confirme"}},
      ]
      b_cols = ["RH_Progesterone", "RH_Oestreogene", "Trait_Radi", "Trait_Chim", "Trait_Horm", "HER2"]
    elif name=="adicap":
      dtype = {
        "code":"string", 
        "libelle":"string"
      }
      rename = {
        "code":"code_adicap",
        "libelle":"adicap"
      }


    # Reading Data Frame
    df = pd.read_csv(archive.open(path), encoding = "latin-1", sep = ";", thousands=" ", decimal=",", dtype = dtype, parse_dates= parse_dates, date_parser = date_parser)
                                                                                                                                                  
    # Transforming know boomlean values                                                                                                           
    for bcol in b_cols:                                                                                                                           
      df[bcol] = df[bcol].map({"Oui": True, "Non": False, "N":False, "O":True, "Négatif":False, "Positif":True, "+":True, "-":False, "P":True, "I":pd.NA, "A":pd.NA, "9":pd.NA, " ":pd.NA})                       
      df[bcol] = df[bcol].astype("boolean")                                                                                                       
                                                                                                                                                  
    # Replacing invalid ages                                                                                                                    
    for acol in a_cols:                                                                                                                           
      df[acol] = df[acol].map(lambda v: int(float(v)) if pd.notna(v) and v != " " and float(v) > 0 and float(v) < 120 else pd.NA).astype(pd.Int64Dtype())                     
                                                                                                                                                  
    # Trabsforming empty to NA                                                                                                                    
    for ncol in n_cols:                                                                                                                           
      df[ncol] = df[ncol].map(lambda v: v if pd.notna(v) and v != " " else pd.NA)                                                                 
      df[ncol] = df[ncol].astype("string")                                                                                                        
                                                                                                                                                  
    # Splitting known string varables into multiple boolean columns                                                                               
    for bcol in to_boolean_cols:                                                                                                                  
      oldcol = df[bcol["col"]]                                                                                                                    
      del df[bcol["col"]]                                                                                                                         
      for value, new in bcol["to"].items():                                                                                                       
        if pd.notna(new):                                                                                                                         
          df[new] = oldcol.map(lambda v: True if v != " " and pd.notna(bcol["to"][v]) and v == value else False)                                  
                                                                                                                                                  
    # Renaminf columns                                                                                                                            
    if len(rename)>0:                                                                                                                             
      df.rename(columns=rename, inplace = True)
  return df

