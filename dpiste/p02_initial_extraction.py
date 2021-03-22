import kskit
import os
import math
import base64
import clipboard
import urllib.parse
from tkinter import Tk
from tkinter import filedialog
from kskit import voo
import kskit.crypto
import kskit.dicom
import tempfile
import subprocess
import pandas as pd
import numpy as np
from dpiste import report
import zipfile
import datetime
from . import dal
from . import utils

def p02_001_generate_neoscope_key():
  """Generate a 256bit random QR code to be used as an AES encryption simmetric key"""
  neo_key_path = utils.get_home("input", "neo","neo_key.png")
  kskit.generate_qr_key(neo_key_path, 32) #32 bytes = 256bits
  print(f"Neoscope extractios key produced on '{neo_key_path}'. Please print too copies of this file, send one to Neoscope operator end delete this file")
  
def p02_002_neoscope_key_to_clipboard():   
  """Use user webcam to copy the neoscope encryption base 64 key to the clipboard"""
  b64key = kskit.crypto.read_webcam_key(auto_close = True, camera_index = 0)
  clipboard.copy(b64key)
  print(f"the key has been copied to the clipboard, put it to the server clipboard and call p02_003_encrypt_neoscope_extractions on it")

def p02_003_encrypt_neoscope_extractions(source, webcam_pwd = True, clipboard_pwd = False):   
  """Encrypts the provided file to the dp_home directory using a clipboard pasted base 64 key"""
  dest = get_home("input", "neo", "extraction_neoscope.aes")
  if webcam_pwd:
    b64key = kskit.crypto.read_webcam_key(auto_close = True, camera_index = 0)
  elif clipboard_pwd:
    b64key = clipboard.paste()
  else:
    raise ValueError("either webcam or clipboard password has to be usef")
  kskit.encrypt(source, dest, b64key)
  #cleaning clipboard
  clipboard.copy("")
  print(f"file has been encrypted and stored on {dest} please proceed delete {source}, send to epiconcept via Epifiles and then remove {dest} too")

def p02_004_send_neoscope_extractions_to_epifiles(epifiles, login, password):
  """Sends the encrypted neoscope extractions to epifiles"""
  source = get_home("input", "neo", "extraction_neoscope.aes")
  dest = f"epi://{urllib.parse.quote_plus(login)}:{urllib.parse.quote_plus(password)}@{epifiles}/extraction_neoscope.aes"
  utils.sparkly_cp(source = source, dest = dest) 

def p02_005_get_neoscope_extractions_from_epifiles(epifiles, login, password):
  """Gets the encrypted neoscope extractions from epifiles"""
  dest = get_home("input", "neo", "extraction_neoscope.aes")
  source = f"epi://{urllib.parse.quote_plus(login)}:{urllib.parse.quote_plus(password)}@{epifiles}/extraction_neoscope.aes"
  utils.sparkly_cp(source = source, dest = dest) 

def p02_006_decrypt_neoscope_extractions(key):   
  """Decrypts the provided file to the dp_home directory using a key pasted on the clipboard"""
  crypted = get_home("input", "neo", "extraction_neoscope.aes")
  orig = get_home("input", "neo", "extraction_neoscope.zip")
  b64key = key 
  kskit.decrypt(crypted, orig, b64key)
  print(f"file has been decrypted and stored on {orig} please proceed delete {crypted} and run the extractions")

def p02_007_get_dicom_guid(esis_host, dataquery, login, password, batch_size, remote_dest = None):
  """
    Executes the esis data query for getting dicomq guids
    data query source code is located here: https://github.com/Epiconcept-Paris/deep.piste/blob/main/dpiste/data/esis.xml
  """
  tdir = tempfile.TemporaryDirectory()
  ldest = get_home("input", "neo",  "esis_dicom_guid.parquet") if remote_dest == None else os.path.join(tdir.name, "esis_dicom_guid.parquet") 
  try:
    df = voo.get_dataset(
      voo_url=esis_host, 
      login=login, 
      password=password, 
      dataset = dataquery, 
      format = "json", 
      order_by = None, 
      batch = batch_size
    )
    df.to_parquet(ldest, "pyarrow")
    if remote_dest != None:
      subprocess.run(["scp", ldest, f"{remote_dest}:{os.path.join(get_home('input', 'neo', 'esis_dicom_guid.parquet'))}"])
  finally:
    tdir.cleanup()

def p02_008_get_dicom(server, port = 11112, retrieveLevel = 'STUDY', page = 1, page_size = 10):
  title = "DCM4CHEE"
  studies = dal.esis.dicom_instance_uid()
  chunks = math.floor(studies.size / page_size)
  uids = [uid for i, uid in enumerate(studies) if i % chunks == page - 1]

  print("getting dicoms")
  for uid in uids:
    dest = get_home("input", "dcm4chee", "dicom", uid) 
    kskit.dicom.get_dicom(key = uid, dest = dest, server = server, port = port, title = title, retrieveLevel = retrieveLevel)
  
  print("producing consolidated dicom dataframe")
  dicom_dir = get_home("input", "dcm4chee", "dicom")
  df = kskit.dicom.dicom2df(dicom_dir)
  
  print("Saving dicom consolidated dataframe")
  dicomdf_dir = os.path.join("input, dcm4chee", "dicom_df")
  df.to_parquet(os.path.join(dicomdf_dir, str(page)), "pyarrow")


def p02_009_neo_stats():
  # Getting a dictionary of expected files 
  entries = p02_009_archive_entries()
  # Getting a dictionary of expected dataframes 
  dfs = dict(p02_009_read_csv(entries.items()))
  pks = {"population":"id_bci", "risque":"id_event", "dépistage":"id_event", "suivi":"id_event", "adicap":"code_adicap", "cim":"id_centre"}
  
  # Forcing pks to become uniques
  for name in dfs.keys():
    nas = dfs[name].loc[pd.isna(dfs[name][pks[name]])]
    print(f"{nas.shape[0]} NAs for {name}[{pks[name]}]")
    dfs[name] = dfs[name].loc[pd.notna(dfs[name][pks[name]])]
    dups = dfs[name][[pks[name]]].groupby(pks[name]).size()
    dups = dups[dups > 1].index.to_list()
    print(f"{len(dups)} duplicates for {name}[{pks[name]}]")
    dfs[name] = dfs[name][~dfs[name][pks[name]].isin(dups)]
    assert dfs[name].shape[0] == dfs[name][pks[name]].nunique(), f"variable {pks[name]} is not unique on  Dataframe {name}"

  # Validating foregn keys
  pks = [
    {"fktable":"suivi", "fkcol":"id_event", "pktable":"dépistage"},
    {"fktable":"suivi", "fkcol":"k_adicap", "pktable":"adicap"},
    {"fktable":"suivi", "fkcol":"k_adicap_1", "pktable":"adicap"},
    {"fktable":"risque", "fkcol":"id_event", "pktable":"dépistage"},
    {"fktable":"dépistage", "fkcol":"id_bci", "pktable":"population"}
  ]

def p02_009_archive_entries():
  #Getting expected filenames from zip files
  with zipfile.ZipFile(utils.get_home("input", "neo", "extraction_neoscope.zip"), "r") as archive:
    matches = {}
    for name in archive.namelist():
      if name.lower().endswith("population.csv"):
        matches["population"]=name
      elif name.lower().endswith("risque ks.csv"):
        matches["risque"]=name
      elif name.lower().endswith("dépistages.csv"):
        matches["dépistage"]=name
      elif name.lower().endswith("suivi.csv"):
        matches["suivi"]=name
      elif name.lower().endswith("adicap ks.csv"):
        matches["adicap"]=name
      elif name.lower().endswith("liste cim.csv"):
        matches["cim"]=name
  return matches

def p02_009_date_parser(d):
  if type(d) == str:
    return datetime.datetime.strptime(d, "%d/%m/%Y")
  elif np.isnan(d):
    return pd.NaT 
  else:
    raise ValueError(f"cannot paser {d} of type {type(d)} as date")

def p02_009_read_csv(entries):
  for name, path in entries:
    with zipfile.ZipFile(utils.get_home("input", "neo", "extraction_neoscope.zip"), "r") as archive:
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
        a_cols = ["Age_ATCD_Cancer","Age_ATCD_Cancer_Bilateral", "Age_ATCD_Chir_Esth", "Age_ATCD_Famil_Mere", "Age_ATCD_Famil_Soeur", "Age_ATCD_Famil_Fille", "Age_ATCD_Famil_Autre"]        
      elif name=="dépistage":
        dtype = {
          "Id_event":pd.Int64Dtype(), 
          "BDI_ACR_SD":"string", 
          "BDI_ACR_SG":"string", 
          "L1_ACR_SG":"string", 
          "L1_ACR_SD":"string", 
          "L2_ACR_SD_SD":"string", 
          "L2_ACR_SD_SG":"string",
          "BDI":"string",
          "resultat_global_L1L2":"string"  
        }
        parse_dates = ["Date_Mammo"]
        to_boolean_cols = [
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
        dtype = {"id_event":pd.Int64Dtype(), "pT": "string", "pN": "string", "localisation":"string", "k_adicap":"string", "k_adicap2":"string", "Grade_SBR":"string", "HER2":"string"}
        parse_dates = ["Date_Mammo", "Date_Anapath", "Date_Inter_Chir", "Date_Radi", "Date_Horm", "Date_Chim"]
        n_cols = ["M", "Si_Malin", "Si_Benin"]
        to_boolean_cols = [
          {"col":"KS_Confirme", "to":{"KS_confirmé":"KS_confirme"}},
        ]
        b_cols = ["RH_Progesterone", "RH_Oestreogene", "Trait_Radi", "Trait_Chim", "Trait_Horm"]
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
      df = pd.read_csv(archive.open(path), encoding = "latin-1", sep = ";", thousands=" ", decimal=",", dtype = dtype, parse_dates= parse_dates, date_parser = p02_009_date_parser)
                                                                                                                                                    
      # Transforming know boomlean values                                                                                                           
      for bcol in b_cols:                                                                                                                           
        df[bcol] = df[bcol].map({"Oui": True, "Non": False, "N":False, "O":True, "Négatif":False, "Positif":True, " ":pd.NA})                       
        df[bcol] = df[bcol].astype("boolean")                                                                                                       
                                                                                                                                                    
      # Replacing invalid ages                                                                                                                    
      for acol in a_cols:                                                                                                                           
        df[acol] = df[acol].map(lambda v: float(v) if pd.notna(v) and v != " " and float(v) > 0 and float(v) < 120 else np.NaN)                     
                                                                                                                                                    
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
    yield (name, df)
                                                                                                                                                  
def p02_010_dicom_guid_report():                                                                                                                  
  report.generate(report = "esis-import")                                                                                                         
                                                                                                                                                  
def p02_011_dicom_report():                                                                                                                       
  report.generate(report = "dcm4chee-import")                                                                                                     
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                
                                                                                                                                                  
                                                                                                                                                  
                                                                                                                                                  
