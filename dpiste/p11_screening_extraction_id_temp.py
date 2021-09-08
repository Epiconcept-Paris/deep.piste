import gnupg
import os
from dpiste import utils
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import getpass
import hashlib

def p11_getGpg():
  path=utils.get_home("data", "transform","hdh", "gpg")
  os.makedirs(name = path, exist_ok = True)
  return gnupg.GPG(gnupghome = path)

def p11_000_generate_fake_transfer_keys(passphrase):
  p11_generate_keys(
    public_path = p11_fake_public_transfer_key_path(), 
    private_path = p11_fake_private_transfer_key_path(), 
    name = 'Deep.pistep_fake_11', 
    email = 'deep.piste.fake.p11@epiconcept.fr', 
    passphrase = passphrase
  )

def p11_001_generate_transfer_keys(passphrase):
  p11_generate_keys(
    public_path = p11_public_transfer_key_path(), 
    private_path = p11_private_transfer_key_path(), 
    name = 'Deep.pistep_11', 
    email = 'deep.piste.p11@epiconcept.fr', 
    passphrase = passphrase
  )

def p11_002_generate_fake_hdh_keys(passphrase):
  p11_generate_keys(
    public_path = p11_fake_hdh_public_key_path(), 
    private_path = p11_fake_hdh_priv_key_path(), 
    name = 'Deep.piste_fake_hdh', 
    email = 'deep.piste.fake_hdh.p11@epiconcept.fr', 
    passphrase = passphrase
  )

def p11_003_encrypt_hdh_extraction_test(passphrase):
  p11_create_test_file_to_crypt(dest = p11_test_tocrypt_file_path(), text = "Hi HDH! from Deep.piste")
  p11_encrypt_and_test(
    source_file =  p11_test_tocrypt_file_path(),
    dest_file = p11_test_crypted_path(),
    from_public_key_path = p11_public_transfer_key_path(), 
    from_private_key_path = p11_private_transfer_key_path(),
    from_passphrase = passphrase, 
    dest_public_key_path = p11_public_hdh_key_path() 
  )

def p11_004_encrypt_and_test_fake_test(sender_passphrase, dest_passphrase):
  p11_create_test_file_to_crypt(dest = p11_fake_tocrypt_file_path(), text = "Hi Epi! all is going smooth here!")
  p11_encrypt_and_test(
    source_file = p11_fake_tocrypt_file_path(),
    dest_file = p11_fake_crypted_path(),
    from_public_key_path = p11_fake_public_transfer_key_path(), 
    from_private_key_path = p11_fake_private_transfer_key_path(),
    from_passphrase = sender_passphrase, 
    dest_public_key_path = p11_fake_hdh_public_key_path(), 
    dest_private_key_path =p11_fake_hdh_priv_key_path() , 
    dest_passphrase = dest_passphrase
  )

def p11_encrypt_and_test(source_file, dest_file, from_public_key_path, from_private_key_path, from_passphrase, dest_public_key_path, dest_private_key_path = None, dest_passphrase = None):
  gpg = p11_getGpg()

  with open(from_private_key_path) as key_file:
    signing_key = gpg.import_keys(key_file.read(), passphrase = from_passphrase)
  gpg.trust_keys(signing_key.fingerprints, "TRUST_ULTIMATE")

  with open(dest_public_key_path) as hdh_key:
    encrypt_key = gpg.import_keys(hdh_key.read())
  gpg.trust_keys(encrypt_key.fingerprints, "TRUST_ULTIMATE")

  with open(source_file, 'rb') as test_file:
    to_crypt = test_file.read()

  #Doing encryption

  encrypted_data = gpg.encrypt(to_crypt, encrypt_key.fingerprints[0], sign=signing_key.fingerprints[0], passphrase = from_passphrase)
  
  print(f"-------------------")
  if encrypted_data.ok == True :
    with open(dest_file, 'w') as crypted_file:
      crypted_file.write(str(encrypted_data))
    print("file encryption SUCCEEDED")
  else:
    print(f"encryption FAILED with {encrypted_data.status}")

  # Doing decryption we will add the destination private key
  # This can only be done if the destination private key has been provided
  if dest_private_key_path is not None and dest_passphrase is not None: 
    # Deleting sender keys and addign only private key to ensure receiver situation
    resp = str(gpg.delete_keys(fingerprints = signing_key.fingerprints[0], secret = True, passphrase = from_passphrase))
    if resp != "ok":
      raise ValueError(f"Private signature could not be removed with the following message {resp}")
    
    resp = str(gpg.delete_keys(fingerprints = signing_key.fingerprints[0], secret = False))
    if resp != "ok":
      raise ValueError(f"Public signature could not be removed with the following message {resp}")
    
    with open(from_public_key_path) as pub_key_file:
      verifying_key = gpg.import_keys(pub_key_file.read())
    gpg.trust_keys(verifying_key.fingerprints[0], "TRUST_ULTIMATE")
    
    # Importing
    with open(dest_file, 'r') as read_crypted_file:
      read_crypted = read_crypted_file.read()

    with open(dest_private_key_path) as hdh_pkey:
      decrypt_key = gpg.import_keys(hdh_pkey.read())
    
    print(f"-------------------")
    decrypted_data = gpg.decrypt(read_crypted, passphrase=dest_passphrase)
    if decrypted_data.ok == True:
      with open(f"{dest_file}.orig", 'wb') as decrypted_file:
        decrypted_file.write(decrypted_data.data)

      with open(f"{dest_file}.orig","rb") as rdec:
        dec_hash =  hashlib.md5(rdec.read()).hexdigest()
      with open(source_file,"rb") as odec:
        orig_hash =  hashlib.md5(odec.read()).hexdigest()
      if dec_hash == orig_hash:
        print(f"Decryption SUCEEDED")
        print(f"md5 hash of file: {orig_hash}")
      else:
        print(f"Decryption FAILED on final checksum test {dec_hash} != {orig_hash}")
    else:
      print(f"Decryption FAILED with {decrypted_data.status}")
    

    print(f"-------------------")
    if decrypted_data.trust_level is not None and decrypted_data.trust_level >= decrypted_data.TRUST_ULTIMATE:
      print("Signature verification SUCCEEED")
      print(f"...........")
      print(f"Signature information") 
      print(f"Username: {decrypted_data.username}") 
      print(f"Key id: {decrypted_data.key_id}") 
      print(f"Signature id: {decrypted_data.signature_id}") 
      print(f"Fingerprint: {decrypted_data.fingerprint}") 
      print(f"Trust Level: {decrypted_data.trust_level}")
      print(f"Trust text: {decrypted_data.trust_text}")
    
      print("file decrypted and validated")
    else :
      print(f"Signature verification FAILED!")
    print(f"-------------------")


  else:
    print("Cannot decrypt or validate since destination private key and passphrase have not been provided")

   
    

  #Comparing resulting file 

def p11_create_test_file_to_crypt(dest, text = "Hi HDH! from Deep.piste"):
  if not os.path.isfile(dest) : 
    # Generating file to crypt
    fnt = ImageFont.truetype('arial.ttf', 15)
    image = Image.new(mode = "RGB", size = (200,70), color = "white")
    draw = ImageDraw.Draw(image)
    draw.text((10,10), text, font=fnt, fill=(0,0,0))
    image.save(dest)

def p11_public_transfer_key_path(): return utils.get_home("data", "output","hdh","p11_transfer_public_key.rsa")
def p11_private_transfer_key_path(): return utils.get_home("data", "output","hdh","p11_transfer_private_key.rsa")
def p11_fake_public_transfer_key_path(): return utils.get_home("data", "output","hdh","fake_crypt", "p11_fake_transfer_public_key.rsa")
def p11_fake_private_transfer_key_path(): return utils.get_home("data", "output","hdh", "fake_crypt", "p11_fake_transfer_private_key.rsa")
def p11_public_hdh_key_path(): return utils.get_home("data", "input", "hdh", "p11_hdh_public.rsa")
def p11_fake_hdh_public_key_path(): return utils.get_home("data", "output", "hdh", "fake_crypt", "p11_fake_hdh_public.rsa")
def p11_fake_hdh_priv_key_path(): return utils.get_home("data", "output", "hdh", "fake_crypt", "p11_fake_hdh_priv.rsa")
def p11_test_tocrypt_file_path(): return utils.get_home("data", "output","hdh", "crypto_test.png")
def p11_fake_tocrypt_file_path(): return utils.get_home("data", "output","hdh", "fake_crypt", "fake_crypto_test.png")
def p11_test_crypted_path(): return utils.get_home("data", "output", "hdh", "p11_test_crypted.png")
def p11_fake_crypted_path(): return utils.get_home("data", "output", "hdh", "fake_crypt", "p11_fake_crypted.png")

def p11_generate_keys(public_path, private_path, name, email, passphrase):
  #randomly generate new private-public RSA key
  #store generaed keys in data/output/hdh/signing-key-public.rsa
  #store generaed keys in data/output/hdh/signing-key-private.rsa
  gpg = p11_getGpg()
  
  if not os.path.isfile(public_path)  or not os.path.isfile(private_path) : 
    # creating the key
    input_data = gpg.gen_key_input(key_type="RSA", key_length=4096, expire_date='2y', name_real=name, name_email=email, passphrase = passphrase)
    key = gpg.gen_key(input_data)

    #exporting public key
    ascii_armored_public_keys = gpg.export_keys(key.fingerprint)
    public = open(public_path, "w")
    public.write(ascii_armored_public_keys)
    public.close()
    
    #exporting private key
    ascii_armored_private_keys = gpg.export_keys(key.fingerprint, secret = True, passphrase = passphrase)
    private = open(private_path, "w")
    private.write(ascii_armored_private_keys)
    private.close()
  else:
    print(f"Keys for {name} exists already, skipping creation")

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
