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
  ldest = get_home("input", "esis",  "esis_dicom_guid.parquet") if remote_dest == None else os.path.join(tdir.name, "esis_dicom_guid.parquet") 
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
      subprocess.run(["scp", ldest, f"{remote_dest}:{os.path.join(get_home('input', 'esis', 'esis_dicom_guid.parquet'))}"])
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


def p02_009_neo_report():
  report.generate(report = "neo-stats")
                                                                                                                                                  
def p02_010_esis_report():                                                                                                                  
  report.generate(report = "esis-import")                                                                                                         
                                                                                                                                                  
def p02_011_dicom_report():                                                                                                                       
  report.generate(report = "dcm4chee-import")                                                                                                     

def p02_012_screening_report():                                                                                                                       
  report.generate(report = "screening-stats")                                                                                                     
