import gnupg
import os
from dpiste import utils
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


def p11_getGpg():
  path=utils.get_home("data", "transform","hdh", "gpg")
  os.makedirs(name = path, exist_ok = True)
  return gnupg.GPG(gnupghome = path)

def p11_001_generate_transfer_keys():
  #randomly generate new private-public RSA key
  #store generaed keys in data/output/hdh/signing-key-public.rsa
  #store generaed keys in data/output/hdh/signing-key-private.rsa
  gpg = p11_getGpg()
  
  if not os.path.isfile(p11_public_transfer_key_path())  or not os.path.isfile(p11_private_transfer_key_path()) : 
    # creating the key
    input_data = gpg.gen_key_input(key_type="RSA", key_length=4096, expire_date='2y', name_real='Deep.pistep_11 ', name_email='deep.piste.p11@epiconcept.fr')
    key = gpg.gen_key(input_data)
    print(input_data)
    print(key)
    #exporting public key
    ascii_armored_public_keys = gpg.export_keys(key.fingerprint)
    public = open(p11_public_transfer_key_path(), "w")
    public.write(ascii_armored_public_keys)
    public.close()
    
    #exporting private key
    ascii_armored_private_keys = gpg.export_keys(key.fingerprint, secret = True, expect_passphrase = False)
    private = open(p11_private_transfer_key_path(), "w")
    private.write(ascii_armored_private_keys)
    private.close()
    print('Keys succesfully created!')
  else:
    print("Keys exists already, skipping creation")


def p11_003_encrypt_hdh_extraction_test():
  # Generating file to crypt
  test_file_path = utils.get_home("data", "transform","hdh", "crypto_test.png")
  fnt = ImageFont.truetype('arial.ttf', 15)
  image = Image.new(mode = "RGB", size = (200,70), color = "white")
  draw = ImageDraw.Draw(image)
  draw.text((10,10), "Hi HDH! from Deep.piste", font=fnt, fill=(0,0,0))
  image.save(test_file_path)
  p11_encrypt_hdh(test_file_path, p11_test_crypted_path())


def p11_encrypt_hdh(unenc_file, enc_file, rmold=False):
  gpg = p11_getGpg()
  with open(p11_private_transfer_key_path()) as key_file:
    signing_key = gpg.import_keys(key_file.read())
  with open(p11_public_hdh_key_path()) as hdh_file:
    encrypt_key = gpg.import_keys(hdh_file.read())
  with open(unenc_file, 'rb') as f:
    to_crypt = f.read()
  #Doing encryption
  encrypted_data = gpg.encrypt(to_crypt, encrypt_key.fingerprints[0], sign=signing_key.fingerprints[0], always_trust=True)
  # If encryption doesn't work, check that you've run "export GPG_TTY=$(tty)"
  if not encrypted_data.ok:
    raise ValueError(f'Encryption failed: {encrypted_data.status}')
  with open(enc_file, 'w') as crypted_file:
    crypted_file.write(str(encrypted_data))
  os.remove(unenc_file) if rmold else None


def p11_decrypt_hdh(enc_file, unenc_file):
  gpg = p11_getGpg()
  with open(enc_file, 'r') as f:
    crypted_data = f.read()
    decrypted_data = gpg.decrypt(crypted_data)
  if not decrypted_data.ok:
    raise ValueError(f'Decryption failed: {decrypted_data.status}')
  with open(unenc_file, 'w') as unencrypted_file:
    unencrypted_file.write(str(decrypted_data))
  return

def p11_public_transfer_key_path(): return utils.get_home("data", "output","hdh","p_11_transfer_public_key.rsa")
def p11_private_transfer_key_path(): return utils.get_home("data", "output","hdh","p_11_transfer_private_key.rsa")
def p11_public_hdh_key_path(): return utils.get_home("data", "output","hdh","p_11_transfer_public_key.rsa")
# def p11_public_hdh_key_path(): return utils.get_home("data", "input", "hdh", "p11_encryption_public.rsa")
def p11_test_crypted_path(): return utils.get_home("data", "output", "hdh", "p11_test_crypted.png")


def p11_004_sygn_hdh_extraction_test():
  raise NotImplementedError()

def p11_005_encrypt_hdh_extraction():
  raise NotImplementedError()
  #generation d un fichier csv data/output/hdh/screening_extraction.csv a partir du resulat de la fonction dal.screening.depistage_pseudo
  #pour developement remplacer le fichier data/transform/screening/depistage_pseudo.parquet par un fichier parquet fige.

def p11_006_sygn_hdh_extraction():
  raise NotImplementedError()

def p11_007_upload_hdh_extractio_sftp_test():
  raise NotImplementedError()

def p11_008_upload_hdh_extractio_sftp():
  raise NotImplementedError()
