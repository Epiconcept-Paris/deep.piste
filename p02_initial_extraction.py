import kskit
import os

def get_home():
  if os.environ.get('DP_HOME') == None :
    raise AssertionError("DP_HOME must be set to run deep.piste scripts")
  else :
    return os.environ.get('DP_HOME')

def p02_001_generate_neoscope_key():
  """Generate a 256bit random QR code to be used as an AES encryption simmetric key"""
  dp_home = get_home()
  neo_key_path = os.path.join(dp_home, "neo_key.png")
  kskit.generate_qr_key(neo_key_path, 32) #32 bytes = 256bits
  print(f"Neoscope extractios key produced on '{neo_key_path}'. Please print too copies of this file, send one to Neoscope operator end delete this file")
  
def p02_002_encrypt_neoscope_extractions(source):   
  """Encrypts the provided file to the dp_home directory using a webcam scanned QR-Code key"""
  dest = os.path.join(get_home(), "extraction_neoscope.aes")
  kskit.encrypt(source, dest)
  print(f"file has been encrypted and stored on {dest} please proceed delete {source}, send to epiconcept via Epifiles and then remove {source} too")

def p02_003_decrypt_neoscope_extractions():   
  """Decrypts the provided file to the dp_home directory using a webcam scanned QR-Code key"""
  crypted = os.path.join(get_home(), "extraction_neoscope.aes")
  orig = os.path.join(get_home(), "extraction_neoscope.orig")
  kskit.decrypt(crypted, orig)
  print(f"file has been decrypted and stored on {orig} please proceed delete {crypted} and run the extractions")

