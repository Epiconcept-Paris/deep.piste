import sys
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from .p02_initial_extraction import *


def main(command):
  if command == "neoscope_key_to_clipboard" :
    p02_002_neoscope_key_to_clipboard() 
  elif command == "encrypt_neoscope_extractions" : 
    get_home() 
    print("Please chose the file to crypt")
    Tk().withdraw()
    filename = askopenfilename()
    
    p02_003_encrypt_neoscope_extractions(filename)   

if __name__ == "__main__":
  main(sys.argv[1])
