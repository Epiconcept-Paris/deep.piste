import gnupg
import os
from dpiste import utils
import pandas as pd

path=utils.get_home("transform","hdh")
gpg = gnupg.GPG(gnupghome = path)
#gpg = gnupg.GPG()

def p11_001_generate_encryption_key():
  #randomly generate new private-public RSA key
  #store generaed keys in data/output/hdh/crypting-key-public.rsa
  #store generaed keys in data/output/hdh/crypting-key-private.rsa
  path_key_public=utils.get_home("data","output","hdh","crypting_key_public.rsa")
  path_key_private=utils.get_home("data","output","hdh","crypting_key_private.rsa")

  input_data = gpg.gen_key_input(key_type="RSA", key_length=4096, expire_date='2y')
  key = gpg.gen_key(input_data)

  if not os.path.isfile(path_key_public) :
    ascii_armored_public_keys = gpg.export_keys(key.fingerprint,passphrase='secret')
    public = open(path_key_public, "a")
    public.write(ascii_armored_public_keys)
    public.close()
  if not os.path.isfile(path_key_private) : 
    ascii_armored_private_keys = gpg.export_keys(key.fingerprint, True,passphrase='secret')
    private = open(path_key_private, "a")
    private.write(ascii_armored_private_keys)
    private.close()

def p11_002_generate_signing_key():
  #randomly generate new private-public RSA key
  #store generaed keys in data/output/hdh/signing-key-public.rsa
  #store generaed keys in data/output/hdh/signing-key-private.rsa
  path_key_public=utils.get_home("data","output","hdh","signing_key_public.rsa")
  path_key_private=utils.get_home("data","output","hdh","signing_key_private.rsa")
  
  input_data = gpg.gen_key_input(key_type="RSA", key_length=4096, expire_date='2y')
  key = gpg.gen_key(input_data)

  if not os.path.isfile(path_key_public) :
    ascii_armored_public_keys = gpg.export_keys(key.fingerprint,passphrase='secret')
    public = open(path_key_public, "a")
    public.write(ascii_armored_public_keys)
    public.close()
  if not os.path.isfile(path_key_private) : 
    ascii_armored_private_keys = gpg.export_keys(key.fingerprint, True,passphrase='secret')
    private = open(path_key_private, "a")
    private.write(ascii_armored_private_keys)
    private.close()

def p11_003_encrypt_hdh_extraction_test():
  entetes = [u'name',u'sexe',u'power']
  valeurs = [
       [u'Superman', u'm', u'Fly'],
       [u'Superwoman', u'f', u'Fly'],
       [u'Hulk', u'm', u'Super Force'],
       [u'Bathman', u'm', u'Fight']
  ]

  f = open(utils.get_home("data","transform","mon_fichier.parquet"), 'w')
  ligneEntete = ";".join(entetes) + "\n"
  f.write(ligneEntete)
  for valeur in valeurs:
       ligne = ";".join(valeur) + "\n"
       f.write(ligne)

  f.close()
  df=pd.read_csv(utils.get_home("data","transform","mon_fichier.parquet"))
  print(df)


def p11_004_sygn_hdh_extraction_test():
  raise NotImplementedError()

def p11_005_encrypt_hdh_extraction():
  #generation d un fichier csv data/output/hdh/screening_extraction.csv a partir du resulat de la fonction dal.screening.depistage_pseudo
  #pour developement remplacer le fichier data/transform/screening/depistage_pseudo.parquet par un fichier parquet fige.

def p11_006_sygn_hdh_extraction():
  raise NotImplementedError()

def p11_007_upload_hdh_extractio_sftp_test():
  raise NotImplementedError()

def p11_008_upload_hdh_extractio_sftp():
  raise NotImplementedError()
