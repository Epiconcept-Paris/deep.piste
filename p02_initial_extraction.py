import kskit
import os
import base64
import clipboard

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
  
def p02_002_neoscope_key_to_clipboard():   
  """Use user webcam to copy the neoscope encryption base 64 key to the clipboard"""
  b64key = kskit.read_webcam_key(auto_close = True, camera_index = 0)
  clipboard.copy(b64key)
  print(f"the key has been copied to the clipboard, put it to the server clipboard and call p02_003_encrypt_neoscope_extractions on it")

def p02_003_encrypt_neoscope_extractions(source):   
  """Encrypts the provided file to the dp_home directory using a clipboard pasted base 64 key"""
  dest = os.path.join(get_home(), "extraction_neoscope.aes")
  b64key = clipboard.paste()
  kskit.encrypt(source, dest, b64key)
  #cleaning clipboard
  clipboard.copy("")
  print(f"file has been encrypted and stored on {dest} please proceed delete {source}, send to epiconcept via Epifiles and then remove {source} too")

def p02_004_decrypt_neoscope_extractions():   
  """Decrypts the provided file to the dp_home directory using a webcam scanned QR-Code key"""
  crypted = os.path.join(get_home(), "extraction_neoscope.aes")
  orig = os.path.join(get_home(), "extraction_neoscope.orig")
  b64key = kskit.read_webcam_key(auto_close = True, camera_index = 0)
  kskit.decrypt(crypted, orig, b64key)
  print(f"file has been decrypted and stored on {orig} please proceed delete {crypted} and run the extractions")

